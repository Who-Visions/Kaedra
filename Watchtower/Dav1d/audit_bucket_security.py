"""
GCS Bucket Security Audit
Check all buckets for public access
"""

import subprocess
import json

BUCKETS = [
    'agent-staging-gen-lang-client-0285887798',
    'ai-studio-bucket-627440283840-us-west1',
    'ai-with-dav3',
    'kaedra-east-gen-lang-client-0285887798',
    'kaedra-gen-lang-client-0285887798',
    'kaedra-logs-east-gen-lang-client-0285887798',
    'kaedra-logs-gen-lang-client-0285887798',
    'kaedra-staging-gen-lang-client-0285887798'
]

print('🔍 Checking GCS Bucket Security...\n')
print('=' * 60)

public_buckets = []
private_buckets = []
errors = []

for bucket in BUCKETS:
    try:
        result = subprocess.run(
            ['gcloud', 'storage', 'buckets', 'get-iam-policy', f'gs://{bucket}', '--format=json'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            policy = json.loads(result.stdout)
            is_public = False
            public_roles = []
            
            for binding in policy.get('bindings', []):
                members = binding.get('members', [])
                role = binding.get('role', '')
                
                # Check for public access
                if 'allUsers' in members or 'allAuthenticatedUsers' in members:
                    is_public = True
                    public_roles.append(role)
            
            if is_public:
                public_buckets.append((bucket, public_roles))
                print(f'❌ SECURITY RISK: {bucket}')
                print(f'   Public roles: {", ".join(public_roles)}')
                print()
            else:
                private_buckets.append(bucket)
                print(f'✅ SECURE: {bucket}')
        else:
            errors.append(bucket)
            print(f'⚠️  ERROR: {bucket} - {result.stderr}')
    
    except Exception as e:
        errors.append(bucket)
        print(f'⚠️  ERROR: {bucket} - {e}')

print('\n' + '=' * 60)
print('📊 SECURITY SUMMARY')
print('=' * 60)
print(f'✅ Secure (Private): {len(private_buckets)}')
print(f'❌ Public: {len(public_buckets)}')
print(f'⚠️  Errors: {len(errors)}')

if public_buckets:
    print('\n🚨 ACTION REQUIRED: The following buckets are PUBLIC:')
    for bucket, roles in public_buckets:
        print(f'   - {bucket} ({", ".join(roles)})')
    print('\nRun secure_buckets.py to fix!')
else:
    print('\n✅ All buckets are properly secured!')

print('=' * 60)
