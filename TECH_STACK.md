# WHO VISIONS LLC - OFFICIAL TECH STACK

**Version**: 1.0
**Last Updated**: 2025-11-26
**Maintained By**: Dave Meralus (SuperDave)
**Agent Access**: ALL AGENTS - Reference this for code generation and execution

---

## 🎯 CRITICAL INSTRUCTION FOR ALL AGENTS

**When building ANY application, website, or code:**
1. **ALWAYS use the exact versions specified below**
2. **NEVER assume or use different versions without explicit permission**
3. **Reference this file before starting any coding task**
4. **Execute code using these exact dependencies**

---

## 📦 FRONTEND STACK

### React Ecosystem

#### **React** - v19.2
- **Official**: Latest React with concurrent features
- **Package**: `react@19.2.0`, `react-dom@19.2.0`
- **Key Features**: Server Components, Actions, use() hook, optimistic updates
- **Usage**: Primary UI library for all web applications

**Installation**:
```bash
npm install react@19.2.0 react-dom@19.2.0
```

**Agent Execution**: When generating React code, use React 19.2 patterns
- Server Components by default
- `use()` for promises and context
- Actions for mutations
- `useOptimistic()` for optimistic UI

---

#### **Next.js** - v16.0.3
- **Official**: Latest Next.js App Router
- **Package**: `next@16.0.3`
- **Key Features**: Partial Prerendering (PPR), Server Actions, enhanced caching
- **Usage**: Primary framework for all web applications

**Installation**:
```bash
npx create-next-app@16.0.3 --typescript --tailwind --app
# OR
npm install next@16.0.3
```

**Project Structure** (App Router):
```
app/
├── layout.tsx       # Root layout
├── page.tsx         # Home page
├── globals.css      # Global styles
└── api/            # API routes
components/
├── ui/             # Shadcn UI components
└── custom/         # Custom components
lib/
├── utils.ts        # Utilities
└── actions.ts      # Server Actions
public/             # Static assets
```

**Agent Execution**: When generating Next.js code:
- Use App Router (app/ directory)
- Server Components by default
- Client Components only when needed ('use client')
- Server Actions for mutations
- Metadata API for SEO

---

### Styling & UI

#### **Tailwind CSS** - v3.4
- **Official**: Utility-first CSS framework
- **Package**: `tailwindcss@3.4`
- **Config**: Extended with custom design system
- **Usage**: Primary styling method for all UI

**Installation**:
```bash
npm install -D tailwindcss@3.4 postcss autoprefixer
npx tailwindcss init -p
```

**tailwind.config.ts** (Standard):
```typescript
import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      // Custom Who Visions LLC design tokens
    },
  },
  plugins: [],
}
export default config
```

---

#### **LightningCSS**
- **Official**: Fast CSS transformer and minifier
- **Package**: `lightningcss`
- **Usage**: CSS optimization and compilation
- **Integration**: Can replace PostCSS for better performance

**Installation**:
```bash
npm install -D lightningcss
```

**Usage with Next.js**:
```javascript
// next.config.js
experimental: {
  cssChunking: 'loose',
}
```

---

#### **Shadcn UI** (Standard Projects)
- **Official**: Accessible component library built on Radix
- **Package**: CLI-based component installation
- **Usage**: Primary component library for standard applications

**Installation**:
```bash
npx shadcn@latest init
```

**Adding Components**:
```bash
npx shadcn@latest add button
npx shadcn@latest add card
npx shadcn@latest add dialog
npx shadcn@latest add form
```

**Agent Execution**: When building standard UI:
1. Use Shadcn components from `components/ui/`
2. Customize with Tailwind classes
3. Follow accessibility best practices
4. Never recreate components that Shadcn provides

---

#### **NyxUI** (Future-Forward Projects)
- **Official**: Modern, animated UI component library
- **Website**: https://nyxui.com/
- **GitHub**: https://github.com/MihirJaiswal/nyxui
- **Components**: https://nyxui.com/components
- **Usage**: For cutting-edge, highly animated, modern projects

**Why NyxUI**:
- ✅ Future-forward design patterns
- ✅ Advanced animations and interactions
- ✅ Modern aesthetic
- ✅ Built with Tailwind CSS
- ✅ TypeScript support

**Installation**:
```bash
npm install nyxui
# Or follow specific component instructions from docs
```

**When to Use NyxUI**:
- Projects requiring modern, cutting-edge UI
- Applications with heavy animation requirements
- Portfolio and showcase projects
- Marketing/landing pages
- Projects where "wow factor" is critical

**When to Use Shadcn UI**:
- Enterprise applications
- Standard business applications
- Projects prioritizing accessibility
- Long-term maintainability focus

**Agent Execution**: Check project requirements:
- **Future-forward/Modern**: Use NyxUI
- **Standard/Enterprise**: Use Shadcn UI
- **Ask Dave** if unsure which to use

---

#### **Radix UI**
- **Official**: Unstyled, accessible component primitives
- **Package**: `@radix-ui/*` (individual packages)
- **Usage**: Foundation for Shadcn UI, use directly when needed

**Key Primitives**:
```bash
npm install @radix-ui/react-dialog
npm install @radix-ui/react-dropdown-menu
npm install @radix-ui/react-popover
npm install @radix-ui/react-select
npm install @radix-ui/react-tabs
```

---

#### **ReactBits** - Latest
- **Official**: React animation components and utilities
- **Website**: https://reactbits.dev/
- **Usage**: PRIMARY animation library for React/Next.js projects

**Why ReactBits**:
- ✅ Production-ready animation components
- ✅ Easy to use, copy-paste components
- ✅ Built with Framer Motion
- ✅ Tailwind CSS compatible
- ✅ TypeScript support
- ✅ Performance optimized

**Categories**:
- Text animations (typewriter, fade in, etc.)
- Hover effects
- Scroll animations
- Loading states
- Transitions
- Interactive elements

**Installation**:
```bash
# ReactBits uses Framer Motion
npm install framer-motion

# Then copy components from reactbits.dev as needed
```

**Usage Example**:
```tsx
import { motion } from 'framer-motion';

export default function AnimatedCard() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="p-6 bg-white rounded-lg shadow-lg"
    >
      <h2 className="text-2xl font-bold">Animated Card</h2>
    </motion.div>
  );
}
```

**Agent Execution**: For animations:
- ALWAYS use ReactBits as primary animation source
- Copy components directly from https://reactbits.dev/
- Use Framer Motion for custom animations
- Maintain performance with proper animation keys
- Follow ReactBits patterns and best practices

---

### Node.js & TypeScript

#### **Node.js** - v25.2.1
- **Official**: JavaScript runtime environment
- **Version**: `25.2.1` (REQUIRED)
- **Usage**: ALL projects must use Node.js 25.2.1
- **Installation**:
```bash
# Using nvm (recommended)
nvm install 25.2.1
nvm use 25.2.1
nvm alias default 25.2.1

# Verify
node --version  # Should output: v25.2.1
```

**Critical**: ALWAYS verify Node.js version before starting any project:
```bash
node --version  # Must be v25.2.1
```

#### **TypeScript** - Latest Stable
- **Official**: Typed superset of JavaScript
- **Package**: `typescript@latest`
- **Config**: Strict mode enabled
- **Usage**: ALL code must be TypeScript (no JavaScript)
- **Runtime**: Use tsx or ts-node for execution

**Installation**:
```bash
npm install -D typescript @types/react @types/node
```

**tsconfig.json** (Standard):
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": false,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

**Agent Execution**:
- NEVER use `any` type
- Always define proper interfaces and types
- Use generics when appropriate
- Leverage type inference

---

## 📱 MOBILE STACK

### React Native

#### **React Native** - Latest Stable
- **Official**: Cross-platform mobile framework
- **Package**: `react-native@latest`
- **Usage**: iOS and Android applications

**Installation**:
```bash
npx react-native init ProjectName --template react-native-template-typescript
```

---

#### **Expo** - Latest SDK
- **Official**: React Native development platform
- **Package**: `expo@latest`
- **Documentation**: https://docs.expo.dev/
- **Usage**: PREFERRED for ALL new mobile projects

**Why Expo**:
- ✅ Fastest way to build React Native apps
- ✅ Over-the-air updates (no app store approval needed)
- ✅ Extensive SDK with native features
- ✅ Expo Router for file-based navigation
- ✅ Expo Go for instant testing on device
- ✅ EAS Build for cloud builds
- ✅ Excellent TypeScript support

**Installation**:
```bash
# Create new Expo project
npx create-expo-app@latest my-app --template

# With TypeScript template
npx create-expo-app@latest my-app --template blank-typescript

# Navigate to project
cd my-app

# Start development server
npx expo start
```

**Project Structure** (with Expo Router):
```
app/
├── (tabs)/          # Tab navigation
│   ├── index.tsx    # Home tab
│   └── profile.tsx  # Profile tab
├── _layout.tsx      # Root layout
└── +not-found.tsx   # 404 page
components/          # React components
constants/           # App constants
hooks/              # Custom hooks
```

**Agent Execution**: For mobile apps:
- **ALWAYS use Expo** unless specific native modules are absolutely required
- Use TypeScript by default
- Use Expo Router for navigation (file-based routing like Next.js)
- Use Expo SDK modules for all native features
- Test with Expo Go app during development
- Build with EAS Build for production

---

#### **NativeWind** - v4 (Latest)
- **Official**: Tailwind CSS for React Native
- **Package**: `nativewind@latest`
- **Website**: https://www.nativewind.dev/
- **Usage**: PRIMARY styling method for ALL mobile projects

**Why NativeWind**:
- ✅ Same Tailwind CSS classes as web
- ✅ Consistent styling between web and mobile
- ✅ Full TypeScript support
- ✅ Works with Expo and React Native CLI

**Installation** (Expo):
```bash
# Create Expo project
npx create-expo-app@latest my-app

cd my-app

# Install NativeWind and dependencies
npm install nativewind
npm install --save-dev tailwindcss@3.4

# Initialize Tailwind config
npx tailwindcss init
```

**tailwind.config.js** (for mobile):
```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./App.{js,jsx,ts,tsx}",
    "./app/**/*.{js,jsx,ts,tsx}",
    "./components/**/*.{js,jsx,ts,tsx}"
  ],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

**babel.config.js**:
```javascript
module.exports = function (api) {
  api.cache(true);
  return {
    presets: [
      ["babel-preset-expo", { jsxImportSource: "nativewind" }]
    ],
    plugins: ["nativewind/babel"],
  };
};
```

**Usage Example**:
```tsx
import { View, Text } from 'react-native';

export default function App() {
  return (
    <View className="flex-1 items-center justify-center bg-white">
      <Text className="text-2xl font-bold text-blue-500">
        Hello NativeWind!
      </Text>
    </View>
  );
}
```

**Agent Execution**: When building mobile apps:
- ALWAYS use NativeWind for styling
- Use same Tailwind classes as web projects
- No StyleSheet.create() - use className prop
- Maintain design consistency with web apps

---

### Kotlin & KMP

#### **Kotlin** - v2.2.21
- **Official**: Modern JVM language
- **Version**: `2.2.21` (REQUIRED)
- **Documentation**: https://kotlinlang.org/docs/home.html
- **Usage**: Android native development, backend services, Kotlin Multiplatform
- **Integration**: Can be called from Node.js

**Build Tools**:
```kotlin
// build.gradle.kts
plugins {
    kotlin("jvm") version "2.2.21"
}
```

**Installation**:
```bash
# Using SDKMAN (recommended)
sdk install kotlin 2.2.21

# Or download from kotlinlang.org
```

**Verification**:
```bash
kotlinc -version
# Should output: Kotlin version 2.2.21
```

---

#### **Kotlin Multiplatform (KMP)** - v2.2.21
- **Official**: Share code between platforms
- **Version**: `2.2.21` (same as Kotlin)
- **Documentation**: https://kotlinlang.org/docs/multiplatform.html
- **Usage**: Shared business logic for iOS/Android/Web/Desktop
- **Integration**: Works with React Native and Expo

**Why KMP**:
- ✅ Share business logic across platforms
- ✅ Write once, run on iOS, Android, Web, Desktop
- ✅ Type-safe native interop
- ✅ Excellent IDE support (IntelliJ IDEA, Android Studio)
- ✅ Gradual adoption - add to existing projects

**Setup** (build.gradle.kts):
```kotlin
plugins {
    kotlin("multiplatform") version "2.2.21"
}

kotlin {
    // Target platforms
    android()
    ios()
    js(IR) {
        browser()
        nodejs()
    }

    // Source sets
    sourceSets {
        val commonMain by getting {
            dependencies {
                implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.8.0")
            }
        }
        val androidMain by getting
        val iosMain by getting
        val jsMain by getting
    }
}
```

**Agent Execution**: When using KMP:
1. Create shared modules in `shared/` directory
2. Platform-specific implementations in respective source sets
3. Bridge to React Native via native modules
4. Use expect/actual for platform-specific code
5. Share networking, data models, business logic

---

## 🎮 3D & GRAPHICS

### Three.js

#### **Three.js** - Latest (r169+)
- **Official**: JavaScript 3D library
- **Documentation**: https://threejs.org/docs/
- **Usage**: PRIMARY library for 3D games, visualizations, and interactive experiences

**Why Three.js**:
- ✅ Industry-standard 3D library for web
- ✅ WebGL abstraction - easier than raw WebGL
- ✅ Extensive documentation and examples
- ✅ Large ecosystem of plugins and tools
- ✅ React integration via @react-three/fiber
- ✅ Performance optimized

**Installation**:
```bash
# Core Three.js
npm install three

# TypeScript types
npm install -D @types/three

# React Three Fiber (for React/Next.js integration)
npm install @react-three/fiber @react-three/drei
```

**Usage Example** (with React Three Fiber):
```tsx
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Box } from '@react-three/drei'

export default function Scene3D() {
  return (
    <div className="h-screen w-full">
      <Canvas>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} />
        <Box args={[1, 1, 1]}>
          <meshStandardMaterial color="hotpink" />
        </Box>
        <OrbitControls />
      </Canvas>
    </div>
  )
}
```

**React Three Fiber Ecosystem**:
- **@react-three/fiber**: React renderer for Three.js
- **@react-three/drei**: Helper components and abstractions
- **@react-three/rapier**: Physics engine
- **@react-three/postprocessing**: Post-processing effects
- **zustand**: State management (recommended by R3F)

**Agent Execution**: For 3D games and graphics:
- Use Three.js for all 3D rendering
- Prefer React Three Fiber when working with React/Next.js
- Use @react-three/drei for common 3D primitives
- Add physics with @react-three/rapier when needed
- Reference Three.js docs for advanced features
- Optimize performance (geometry instancing, LOD, etc.)

**Common Use Cases**:
- 3D games
- Product visualizations
- Interactive experiences
- Data visualizations in 3D
- Virtual tours
- AR/VR experiences

---

## 🔧 SUPPORTING TOOLS

### Package Management
- **npm** (primary)
- **pnpm** (for monorepos)
- **Yarn** (legacy support only)

### Build Tools
- **Vite** (for non-Next.js projects)
- **Turbo** (for monorepos)
- **Webpack** (Next.js internal)

### Testing
- **Vitest** (unit/integration)
- **Playwright** (E2E)
- **Jest** (legacy support)

### Code Quality
- **ESLint** (linting)
- **Prettier** (formatting)
- **TypeScript** (type checking)

---

## 🏗️ ARCHITECTURE FRAMEWORKS

**Note**: Custom Who Visions LLC architecture patterns will be added here as they are developed.

### Future Additions:
- [ ] Authentication patterns
- [ ] Database schemas and ORMs
- [ ] API design patterns
- [ ] State management patterns
- [ ] Component architecture
- [ ] Deployment configurations
- [ ] Monitoring and logging
- [ ] Performance optimization patterns

---

## 📋 AGENT EXECUTION PROTOCOLS

### Before Starting Any Coding Task:

1. **Verify Tech Stack**:
   - Check this file for exact versions
   - Confirm dependencies match specification
   - Update if this file has been modified

2. **Setup Project**:
   ```bash
   # For web apps
   npx create-next-app@16.0.3 --typescript --tailwind --app
   cd project-name
   npx shadcn@latest init

   # For mobile apps
   npx create-expo-app@latest --template
   ```

3. **Install Dependencies** (exact versions):
   ```bash
   npm install react@19.2.0 react-dom@19.2.0
   npm install next@16.0.3
   npm install -D tailwindcss@3.4 postcss autoprefixer
   npm install -D typescript @types/react @types/node
   ```

4. **Configure Environment**:
   - Set up TypeScript strict mode
   - Configure Tailwind with design tokens
   - Initialize Shadcn UI
   - Set up ESLint and Prettier

5. **Code Generation**:
   - Use TypeScript exclusively
   - Follow Next.js 16 App Router patterns
   - Use Server Components by default
   - Style with Tailwind utility classes
   - Use Shadcn components when available

---

## 🚨 CRITICAL RULES

### DO:
✅ Use Node.js 25.2.1 (verify with `node --version`)
✅ Use exact versions specified above
✅ Reference this file before every coding task
✅ Use TypeScript for ALL code
✅ Use Shadcn UI components (web)
✅ Use Tailwind CSS for styling (web)
✅ Use NativeWind for styling (mobile)
✅ Use Server Components in Next.js
✅ Use Expo for mobile projects

### DON'T:
❌ Use different Node.js version (MUST be 25.2.1)
❌ Use different package versions without approval
❌ Write JavaScript (must be TypeScript)
❌ Use inline styles (use Tailwind/NativeWind)
❌ Use StyleSheet.create() in React Native (use NativeWind)
❌ Recreate components that Shadcn provides
❌ Use Class components (use Hooks)
❌ Use Pages Router (use App Router)
❌ Use CSS Modules (use Tailwind)

---

## 📚 REFERENCE LINKS

### Core Stack
- **Node.js**: https://nodejs.org
- **React 19**: https://react.dev
- **Next.js 16**: https://nextjs.org
- **TypeScript**: https://typescriptlang.org

### Styling & UI (Web)
- **Tailwind CSS v3**: https://v3.tailwindcss.com/
- **Shadcn UI**: https://ui.shadcn.com
- **NyxUI**: https://nyxui.com/ (future-forward)
- **ReactBits**: https://reactbits.dev/ (animations)
- **Radix UI**: https://radix-ui.com

### Mobile
- **React Native**: https://reactnative.dev
- **Expo**: https://expo.dev
- **NativeWind**: https://www.nativewind.dev/

### 3D & Graphics
- **Three.js**: https://threejs.org/docs/
- **React Three Fiber**: https://r3f.docs.pmnd.rs/getting-started/introduction

### Other
- **Kotlin**: https://kotlinlang.org

---

## 🔄 VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.3 | 2025-11-26 | Added ReactBits for animations, Added Three.js for 3D games/graphics |
| 1.2 | 2025-11-26 | Added NativeWind v4 for mobile styling, Added NyxUI for future-forward projects, Specified Kotlin 2.2.21, Added KMP documentation |
| 1.1 | 2025-11-26 | Added Node.js 25.2.1 requirement, updated Tailwind docs link |
| 1.0 | 2025-11-26 | Initial tech stack definition |

---

**THIS IS THE OFFICIAL WHO VISIONS LLC TECH STACK**
**ALL AGENTS MUST REFERENCE AND FOLLOW THIS SPECIFICATION**
