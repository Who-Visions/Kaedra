# Notion Links Inspection

## [DATABASE] Shadow Dweller Prequel Scenes
**ID**: `2e5ca671311e816384e6dfd56a5306fe`
### Properties
- **Word Count** (`number`)
- **Revision Notes** (`rich_text`)
- **Intensity Rating** (`select`)
  - Options: PG-13, R, NC-17
- **Read Time Estimate** (`number`)
- **Act** (`select`)
  - Options: Act I, Act II, Act III, Epilogue
- **Outcome Type** (`select`)
  - Options: Displacement, Death, Injury, Discovery, Betrayal, Extraction, Cover Up
- **POV** (`select`)
  - Options: Xoah, Corbin, Ravenous, Nyx, Vale Rook, Omni
- **Tone** (`multi_select`)
  - Options: Horror, Crime, Thriller, Sci-Fi, Action, Noir
- **Mechanic Trigger** (`select`)
  - Options: Blood Transfer, Touch, Proximity, Veil Pulse, Dampener Override, Oracle Static
- **Canon Lock** (`checkbox`)
- **Age of Xoah** (`number`)
- **Timeline Date** (`date`)
- **Factions Present** (`multi_select`)
  - Options: Crows, Syndicate, BVL, Resistance, MPF, Independent, Unknown
- **Continuity Flags** (`rich_text`)
- **Volume** (`select`)
  - Options: Vol 1, Vol 2, Vol 3, Vol 4
- **Draft Status** (`select`)
  - Options: Outline, First Draft, Revision, Final
- **Evidence Produced** (`multi_select`)
  - Options: Sensor Spike, Blood Sample, Photo, Scan, Ledger Entry, Rumor, Body, No Body
- **Cover Story** (`rich_text`)
- **Scene Title** (`title`)

## [DATABASE] Shadow Dweller Scenes
**ID**: `2e5ca671311e81e1aca3ee6936a11490`
### Properties
- **Act** (`select`)
  - Options: Act I - Ordinary World, Act II - Trials & Tribulation, Act III - Resolution, Prologue, Epilogue, Interlude
- **Next Scene** (`rich_text`)
- **Location** (`rich_text`)
- **Status** (`status`)
  - Options: Draft, Outline, In Review, Revising, Final
- **Volume** (`select`)
  - Options: Volume I, Volume II, Volume III, Volume IV, Volume V, Volume VI, Volume VII, Standalone
- **Time** (`rich_text`)
- **Character Focus** (`multi_select`)
  - Options: Protagonist, Antagonist, Ally, Mentor, Love Interest, Rival, Side Character, Villain
- **Thematic Core** (`rich_text`)
- **Canon Locks** (`multi_select`)
  - Options: Major Plot Points, Character History, Timeline Anchor, Worldbuilding Element, Established Relationships, Fixed Locations, Critical Lore
- **Visual Direction** (`rich_text`)
- **Scene Title** (`title`)
- **Factions Present** (`multi_select`)
  - Options: Crows, Syndicate, BVL, Resistance, MPF, Independent, Unknown
- **Age of Xoah** (`number`)
- **Evidence Produced** (`multi_select`)
  - Options: Sensor Spike, Blood Sample, Photo, Scan, Ledger Entry, Rumor, Body, No Body
- **POV** (`select`)
  - Options: Xoah, Corbin, Ravenous, Nyx, Vale Rook, Omni
- **Intensity Rating** (`select`)
  - Options: PG-13, R, NC-17
- **Word Count** (`number`)
- **Cover Story** (`rich_text`)
- **Timeline Date** (`date`)
- **Continuity Flags** (`rich_text`)
- **Mechanic Trigger** (`select`)
  - Options: Blood Transfer, Touch, Proximity, Veil Pulse, Dampener Override, Oracle Static
- **Draft Status** (`select`)
  - Options: Outline, First Draft, Revision, Final
- **Canon Lock** (`checkbox`)
- **Outcome Type** (`select`)
  - Options: Displacement, Death, Injury, Discovery, Betrayal, Extraction, Cover Up
- **Tone** (`multi_select`)
  - Options: Horror, Crime, Thriller, Sci-Fi, Action, Noir

## [DATABASE] Lore Laws
**ID**: `2e5ca671311e81bca466f254e515a7f7`
### Properties
- **Rule Statement** (`rich_text`)
- **Known Exceptions** (`rich_text`)
- **Enforcement Level** (`select`)
  - Options: Hard Rule, Soft Rule, Myth Rule
- **Status** (`select`)
  - Options: Draft, Active Canon, Deprecated, Retconned
- **Canon Lock** (`checkbox`)
- **Contradictions** (`relation`)
- **Expanded Explanation** (`rich_text`)
- **Law Name** (`title`)

## [DATABASE] Timeline Nodes
**ID**: `2e5ca671311e816fbb30d898aa7de7c9`
### Properties
- **Canon Notes** (`rich_text`)
- **Date or Relative Order** (`number`)
- **Canon Lock** (`checkbox`)
- **Status** (`select`)
  - Options: Draft, Active Canon, Deprecated, Retconned
- **Node Type** (`select`)
  - Options: Historical, Story Present, Flashback, Prophecy
- **Era** (`select`)
  - Options: Pre-History / Void Era, Ancient Era, Classical Era, Modern Era, Future Era, Post-Apocalyptic Era, Timeless / Outside Time
- **Node Name** (`title`)

## [DATABASE] VeilVerse Ingestion Queue
**ID**: `2e5ca671311e81c781bbd5a3bb857f4c`
### Properties
- **Recursion Layer Guess** (`select`)
  - Options: Layer 0, Layer 1, Layer 2, Layer 3, Layer 4
- **Summary written** (`checkbox`)
- **Tags** (`multi_select`)
- **Source Type** (`select`)
  - Options: YouTube, Article, Book, Note, Brainstorm, Chat Log, Other
- **Duplicates checked** (`checkbox`)
- **Source Page ID** (`rich_text`)
- **Status** (`select`)
  - Options: New, Parsed, Needs Review, Approved, Imported, Rejected
- **Type assigned** (`checkbox`)
- **Reviewer Notes** (`rich_text`)
- **Source URL** (`url`)
- **Captured On** (`created_time`)
- **Recursion Layer set** (`checkbox`)
- **Notion AI Extract** (`rich_text`)
- **Truth Grade Guess** (`select`)
  - Options: Confirmed, Inferred, Rumor, Propaganda
- **Duplicate Risk** (`select`)
  - Options: Low, Medium, High
- **Conflicts Flagged** (`checkbox`)
- **Conflicts checked** (`checkbox`)
- **Links added** (`checkbox`)
- **Raw Notes** (`rich_text`)
- **Ready to import** (`checkbox`)
- **Truth Grade set** (`checkbox`)
- **Title** (`title`)

## [PAGE] 2e5ca671311e81d2af92cfbd6074f04a
**ID**: `2e5ca671311e81d2af92cfbd6074f04a`

## [DATABASE] Veil Verse Science
**ID**: `2e5ca671311e8146801edc1801ebad78`
### Properties
- **Notes** (`rich_text`)
- **Hardness** (`select`)
  - Options: Soft Magic, Mild, Grounded, Firm, Hard Physics
- **Development Status** (`select`)
  - Options: Draft, Provisional, Verified, Canon Locked
- **Sub-Categories** (`multi_select`)
  - Options: Veil Physics, Energy Systems, Materials Science, Biology, Neuroscience, Infrastructure, Weapons Tech, Propulsion, Sensors, Computing, Medicine, Ecology, Temporal Tech, Social Tech, Security, Ritual Interface
- **Visual Reference** (`url`)
- **Description** (`rich_text`)
- **Task Notes** (`rich_text`)
- **Last Updated** (`date`)
- **Category** (`select`)
  - Options: Veil, Mars Infra, Human Bio, Weapons, Transit, Computation, Environment
- **World Impact** (`select`)
  - Options: Minor, Moderate, Major, Fundamental, Revolutionary
- **Priority** (`select`)
  - Options: Low, Medium, High, Critical
- **Concept Name** (`title`)

## [DATABASE] 🎓 Film Education Library
**ID**: `2e5ca671311e81ae885ac535308c72c1`
### Properties
- **Key Takeaways** (`rich_text`)
- **Source URL** (`url`)
- **Format** (`select`)
  - Options: Video, Article, Course, Book, Podcast, Case Study
- **Notes** (`rich_text`)
- **Topic** (`multi_select`)
  - Options: Cinematography, Directing, Editing, Production Design, Sound Design, Screenwriting, Acting, Producing, Lighting, VFX, Color Grading, Camera Movement, Composition, Storytelling, Genre Study, Film History, Industry
- **Date Added** (`date`)
- **Description** (`rich_text`)
- **Relevant To** (`multi_select`)
  - Options: Pre-Production, Production, Post-Production, Development, Distribution, All Phases
- **Priority** (`select`)
  - Options: Must Watch, High, Medium, Low, Reference
- **Title** (`title`)

## [DATABASE] Canon Registry
**ID**: `2e5ca671311e8130aee3fec81576cc01`
### Properties
- **Linked Records** (`relation`)
- **Tags** (`multi_select`)
- **Truth Grade** (`select`)
  - Options: Confirmed, Inferred, Rumor, Propaganda
- **Recursion Layer** (`select`)
  - Options: Layer 0, Layer 1, Layer 2, Layer 3, Layer 4
- **Type** (`select`)
  - Options: Character, Faction, Location, Artifact, Event, Scene, Concept, Law, Media, Timeline Node
- **Created Date** (`created_time`)
- **Summary** (`rich_text`)
- **Status** (`select`)
  - Options: Draft, Active Canon, Deprecated, Retconned
- **Last Updated** (`date`)
- **Canon Lock** (`checkbox`)
- **Migrated On** (`date`)
- **Name** (`title`)

## [DATABASE] The Ledger
**ID**: `2e5ca671311e81368083ecd615826400`
### Properties
- **Escalation Ladder** (`select`)
  - Options: Soft Pressure, Access Denial, Reputation Pressure, Legal Pressure, Physical Pressure, Termination
- **Source Notes** (`rich_text`)
- **Entry Type** (`select`)
  - Options: Incident, Debt, Favor, Asset, Witness, Artifact Custody, Narrative Control
- **Factions Touched** (`multi_select`)
  - Options: Crows, Syndicate, BVL, Resistance, MPF, Independent, Unknown
- **Private Ledger Truth** (`rich_text`)
- **Status** (`status`)
  - Options: Open, Dormant, Burning, Settled
- **Public Record** (`rich_text`)
- **Settlement Options** (`rich_text`)
- **Date of Event** (`date`)
- **Leverage Tags** (`multi_select`)
  - Options: Medical Debt, Contamination Flag, Housing Hold, Employment Hold, Oxygen Access, Transit Access, Blackmail, Custody Object, Oracle Static
- **Ledger Entry ID** (`title`)

## [PAGE] 2e5ca671311e813f884ce2f606069dfa
**ID**: `2e5ca671311e813f884ce2f606069dfa`

## [PAGE] 2e5ca671311e81c1a1e9c84bcf4ee95d
**ID**: `2e5ca671311e81c1a1e9c84bcf4ee95d`

## [PAGE] 2e5ca671311e81c9a381d50da194f4df
**ID**: `2e5ca671311e81c9a381d50da194f4df`

## [PAGE] 2e5ca671311e81d4bbf1d9a470a3a4ec
**ID**: `2e5ca671311e81d4bbf1d9a470a3a4ec`

## [DATABASE] News Projects
**ID**: `2e5ca671311e81548a85fbda79c83f38`
### Properties
- **Assignment Date** (`date`)
- **Publish Date** (`date`)
- **Links** (`url`)
- **Type** (`multi_select`)
  - Options: Breaking News, Feature Story, Documentary, Interview, Event Coverage, Investigation, Opinion/Commentary, Photo Essay, Video Report
- **Location** (`rich_text`)
- **Subject/Beat** (`multi_select`)
  - Options: Politics, Business, Tech, Culture, Arts, Community, Sports, Entertainment, Social Justice, Environment, Fashion, Gaming, Anime/Cosplay, Music
- **Coverage Date** (`date`)
- **Assets** (`multi_select`)
  - Options: Photos Needed, Video Needed, Audio Needed, Graphics Needed, B-Roll Needed, Interviews Scheduled, Research Complete
- **Payment Status** (`select`)
  - Options: Not Applicable, Quoted, Invoiced, Paid, Issue
- **Deadline** (`date`)
- **Collaborators** (`people`)
- **Notes** (`rich_text`)
- **Contract Status** (`select`)
  - Options: Not Needed, Pending, Signed, Issue
- **Publication/Outlet** (`rich_text`)
- **Priority** (`select`)
  - Options: Low, Medium, High, Critical
- **Status** (`select`)
  - Options: Inbox, Pitching, In Progress, Editing, Published, Archived
- **Project Name** (`title`)

## [DATABASE] VeilVerse Goals
**ID**: `2e5ca671311e81eb9b5eed4a4ba7ffd9`
### Properties
- **Milestones** (`rich_text`)
- **Last Reviewed** (`date`)
- **Year** (`select`)
  - Options: 2026, 2027, 2028, 2029, 2030
- **Success Metrics** (`rich_text`)
- **Timeline** (`select`)
  - Options: 1-Year Vision, 3-Year Vision, 5-Year Vision, 10-Year Vision
- **Obstacles** (`rich_text`)
- **Status** (`status`)
  - Options: Draft, Proposed, In Progress, Blocked, Done, Archived
- **If-Then Intentions** (`rich_text`)
- **Progress %** (`number`)
- **Goal Type** (`select`)
  - Options: Story Development, Canon Governance, Production Systems, Community Building, Technical Infrastructure, Business/Monetization, Personal Creative Health
- **Deadline** (`date`)
- **Owner** (`people`)
- **Priority** (`select`)
  - Options: Critical, High, Medium, Low
- **Goal Statement** (`title`)

## [DATABASE] VeilVerse Goals
**ID**: `2e5ca671311e81368004c1a40c809070`
### Properties
- **Milestones** (`rich_text`)
- **Last Reviewed** (`date`)
- **Year** (`select`)
  - Options: 2026, 2027, 2028, 2029, 2030
- **Success Metrics** (`rich_text`)
- **Timeline** (`select`)
  - Options: 1-Year Vision, 3-Year Vision, 5-Year Vision, 10-Year Vision
- **Obstacles** (`rich_text`)
- **Status** (`status`)
  - Options: Draft, Proposed, In Progress, Blocked, Done, Archived
- **If-Then Intentions** (`rich_text`)
- **Progress %** (`number`)
- **Goal Type** (`select`)
  - Options: Story Development, Canon Governance, Production Systems, Community Building, Technical Infrastructure, Business/Monetization, Personal Creative Health
- **Deadline** (`date`)
- **Owner** (`people`)
- **Priority** (`select`)
  - Options: Critical, High, Medium, Low
- **Goal Statement** (`title`)

## [PAGE] 2e5ca671311e8187bd69f8768b4b6218
**ID**: `2e5ca671311e8187bd69f8768b4b6218`

## [PAGE] 2e5ca671311e815bac95ff6269578ff3
**ID**: `2e5ca671311e815bac95ff6269578ff3`

## [PAGE] 2e5ca671311e81e2ae43d3d78b3881ad
**ID**: `2e5ca671311e81e2ae43d3d78b3881ad`

## [PAGE] 2e5ca671311e81cb89b8c19821907cce
**ID**: `2e5ca671311e81cb89b8c19821907cce`

## [DATABASE] VeilVerse Universe Best
**ID**: `2e5ca671311e811fb3d7c7f3b9150afe`
### Properties
- **Appears In** (`multi_select`)
  - Options: Volume 1, Volume 2, Volume 3, Volume 4, Volume 5, Prologue Arc, Interlude Arc, Canon Registry, Pilot, Season 1, Season 2, DLC, Mainline, One Shot
- **Duplicates** (`relation`)
- **Duplicate Of** (`relation`)
- **Veil Rule Link** (`relation`)
- **Media Type** (`multi_select`)
  - Options: Screenplay, Storyboard, Animatic, Visual Bible, Lore Bible, Music, Podcast, ARG, Tabletop, VR/XR, Interactive Fiction
- **Universe Era** (`select`)
  - Options: Pre Collapse Era, Collapse Era, Reconstruction Era, Near Future Era, Far Future Era, Deep Time Era
- **Render Status** (`status`)
  - Options: Not Started, Briefing, Prompting, Rendering, Polishing, Approved, Archived
- **Creator/Writer** (`rich_text`)
- **Canon Confidence** (`number`)
- **Negative Prompt** (`rich_text`)
- **Veil Presence Level** (`number`)
- **Relationships** (`rich_text`)
- **Affiliation** (`rich_text`)
- **Image** (`url`)
- **Mood Board Links** (`url`)
- **Veil Primary Tell** (`rich_text`)
- **Species/Race** (`multi_select`)
  - Options: Cyborg, Bio Engineered, Undead, Demon, Angelic, Fae, Djinn, Ancient Machine, Parasite Bonded, Veilborn
- **Timeline Start Year** (`number`)
- **Story Arc** (`select`)
  - Options: Inciting Incident, Trials, Midpoint Shift, Dark Night, Finale, Aftermath, Flashback, Foreshadow Thread
- **Chronology Notes** (`rich_text`)
- **Prompt Pack** (`rich_text`)
- **Alias** (`multi_select`)
  - Options: Shadow Courier, The Shadow King, First Shadow King
- **Timeline End Year** (`number`)
- **Continuity Flags** (`multi_select`)
  - Options: Contradiction, Missing Source, Timeline Clash, Duplicate, Needs Retcon, Unclear Motive
- **First Appearance** (`rich_text`)
- **Veil Activation Trigger** (`rich_text`)
- **Canon Status** (`select`)
  - Options: Soft Canon, Pending Review, Contradicted, Replaced, Canon Locked
- **Abilities/Powers** (`rich_text`)
- **Power Level** (`select`)
  - Options: Human Plus, City Level, Planetary, Multiversal
- **Slug** (`rich_text`)
- **Node Tier** (`select`)
  - Options: Tier 1, Tier 2, Tier 3, Background
- **Color Palette** (`multi_select`)
  - Options: Neon, Ash, Gold, Crimson, Violet, Cyan, Obsidian, Bone, Rust, Emerald
- **Veil Failure Mode** (`rich_text`)
- **Home World** (`rich_text`)
- **Category** (`select`)
  - Options: Organization, Culture, Creature, Vehicle, Language, Religion, Planet, Dimension, System, Law, Scene, Symbol
- **Veil Secondary Tells** (`rich_text`)
- **Notes** (`rich_text`)
- **ID** (`unique_id`)
- **Parent Organization** (`rich_text`)
- **Entity Subtype** (`multi_select`)
  - Options: Protagonist, Antagonist, Mentor, Courier, Assassin, Scientist, AI, Oracle, Warlord, City, District, Corridor, Market, Shrine, Vault, Museum, Slum, Sanctum, Transit Node, Syndicate, Resistance Cell, Cult, Corporation, Government, Mercenary Band, Weapon, Veil Shard, Relic, Key, Suit, Consumable, Contract Sigil, Heist, Uprising, Assassination, Collapse, Discovery, Trial, Betrayal, War, Protocol, Ritual, Interface, Engine, Binding, Surveillance Stack
- **Series/Franchise** (`multi_select`)
  - Options: VeilVerse Core, VeilVerse Alternate, Spin-off, Prequel Era, Sequel Era, Anthology, Crossover, Standalone, Shadow Dweller Saga, Echo Runners, Veil Seekers
- **Veil Consequences** (`rich_text`)
- **Tags** (`multi_select`)
  - Options: Render Ready, Needs Visual, Needs Timeline, Needs Connections, Needs Powers, Continuity Risk, Retcon Candidate, Anchor Node, Scene Critical, Template Seed
- **Anchor Node** (`checkbox`)
- **Connected To 1** (`relation`)
- **Era Detail** (`select`)
- **Visual Brief** (`rich_text`)
- **Location** (`rich_text`)
- **Connection Notes** (`rich_text`)
- **Continuity Notes** (`rich_text`)
- **Cinematography Tags** (`multi_select`)
  - Options: Handheld, Dolly, Wide, Macro, Long Lens, Shallow DOF, Noir Contrast, Volumetric Haze
- **Production Status** (`select`)
  - Options: Concept, In Development, Pre-Production, In Production, Post-Production, Released, Archived, Cancelled
- **Canon Weight** (`select`)
  - Options: Prime, Core, Peripheral, Experimental, Alt Layer
- **Model Target** (`select`)
  - Options: Nano Banana Pro, Gemini Image, Midjourney, Firefly, Stable Diffusion, Practical Shoot
- **Timeline Year** (`number`)
- **Veil Cost** (`rich_text`)
- **Linked By Law** (`relation`)
- **Importance** (`select`)
  - Options: Major, Supporting, Minor, Background
- **Connection Type** (`multi_select`)
  - Options: Ally, Enemy, Family, Mentor, Rival, Owner Of, Created By, Located In, Part Of, Leads, Serves, Seeks, Hunts, Protects, Betrayed By, Bound To
- **Display Name** (`rich_text`)
- **Connected To** (`relation`)
- **Importance Score** (`number`)
- **Asset Folder** (`url`)
- **Themes** (`multi_select`)
  - Options: Control, Freedom, Class Divide, Surveillance, Trauma, Myth, Faith, Corruption, Loyalty, Memory, Destiny, Chaos
- **Description** (`rich_text`)
- **Last Updated** (`date`)
- **Aspect Ratio** (`select`)
  - Options: 1:1, 4:5, 16:9, 9:16, 3:2, 2:3
- **Status** (`status`)
  - Options: Unknown, Active, Inactive, Completed
- **Timeline Precision** (`select`)
  - Options: Exact, Estimated, Range, Mythic, Unknown
- **Source URL** (`url`)
- **Name** (`title`)
- **URL** (`url`)
- **ChatTime** (`date`)
- **Google Drive File** (`relation`)
- **GitHub Pull Requests** (`relation`)