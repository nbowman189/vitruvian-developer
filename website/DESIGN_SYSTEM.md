# The Vitruvian Developer - Design System

## Vision
Create a cohesive personal brand platform that showcases the intersection of software engineering, AI development, and physical discipline through integrated design, compelling storytelling, and strategic content hierarchy.

---

## Color Palette

### Primary Brand Colors
- **Deep Navy Blue (#1a237e):** Technology, Code, Engineering
- **Deep Purple (#422c4d):** AI, Mind, Intellect
- **Warm Orange (#ff8a3d):** Energy, Fitness, Discipline

### Discipline-Specific Colors
- **Code:** `#1a237e` (Deep Blue)
- **AI:** `#7c3aed` (Purple)
- **Fitness:** `#ff8a3d` (Orange)
- **Meta/Philosophy:** `#06b6d4` (Cyan)

### Gradients
- **Primary Gradient:** Navy Blue → Deep Purple (Tech + AI)
- **Accent Gradient:** Orange → Red (Energy + Intensity)
- **Synergy Gradient:** Navy Blue → Purple → Orange (All disciplines)

---

## Typography

### Font Family
System fonts: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto`
- Clean, professional, highly readable
- Allows for custom geometric fonts as future enhancement

### Heading Hierarchy
- **H1:** 2.5rem, 800 weight, -1.5px letter spacing
- **H2:** 2rem, 700 weight, -0.5px letter spacing
- **H3:** 1.5rem, 600 weight
- **H4:** 1.25rem, 600 weight

### Body Text
- Line height: 1.6
- Color: #1a1a1a (dark)
- Secondary text: #6b7280 (light gray)
- Muted text: #9ca3af (muted gray)

---

## Component Library

### Tags/Badges
#### Discipline Tags
```html
<span class="tag tag-code">Code</span>
<span class="tag tag-ai">AI</span>
<span class="tag tag-fitness">Fitness</span>
<span class="tag tag-meta">Meta</span>
```

Styling:
- Light background with discipline color
- Bordered for definition
- Border radius: 20px
- Font size: 0.85rem, weight: 600

#### Synergy Badge
```html
<div class="synergy-badge">🔗 Synergy: Code + AI + Fitness</div>
```

Shows when content bridges multiple disciplines.

### Cards
#### Discipline-Accent Cards
```html
<div class="card card-accent-code"><!-- Content --></div>
<div class="card card-accent-ai"><!-- Content --></div>
<div class="card card-accent-fitness"><!-- Content --></div>
```

Features:
- Left border (4px) in discipline color
- Creates visual category system
- Works with all card types

### Highlights
#### Inline Discipline References
```html
<span class="highlight-code">Code</span>
<span class="highlight-ai">AI</span>
<span class="highlight-fitness">Fitness</span>
```

Usage:
- Highlight discipline mentions in text
- Light colored background
- Discipline-specific color text

### Section Dividers
```html
<div class="section-divider"></div>
```

Features:
- Synergy gradient
- Visual break between sections
- Emphasizes flow and connection

---

## Design Principles

### 1. Synergy First
Every design decision should reflect how disciplines interconnect. Visual elements should suggest relationships and reinforce the theme of integrated excellence.

### 2. Story Over Stats
Emphasize narrative and impact over listing credentials. Project case studies and blog posts should tell compelling stories about why work matters.

### 3. Clarity with Personality
Professional and polished while distinctly reflecting Nathan's personality. Modern but not trendy. Timeless but current.

### 4. Color as Communication
Use discipline colors strategically:
- Blog posts tagged with their primary discipline
- Projects color-coded by focus area
- Navigation subtly reflects current section

### 5. Consistency & Harmony
- Unified spacing system (8px grid)
- Shadow hierarchy (sm, md, lg, xl)
- Transitions (0.2s-0.3s ease)
- Border radius (6px standard, 20px for badges)

---

## Component Specifications

### Shadows
- **Small:** `0 1px 2px rgba(0, 0, 0, 0.05)`
- **Medium:** `0 4px 12px rgba(0, 0, 0, 0.1)`
- **Large:** `0 10px 25px rgba(0, 0, 0, 0.15)`
- **Extra Large:** `0 20px 40px rgba(0, 0, 0, 0.2)`

### Spacing
- Base unit: 0.5rem (8px)
- Sections: 2-3rem vertical spacing
- Content: 1.5rem padding
- Gaps: 1rem - 1.5rem

### Border Radius
- Cards: 6px
- Badges: 20px
- Buttons: 6px
- Images: 8px

### Transitions
- Standard: 0.2s ease (hover effects)
- Navigation: 0.3s ease (nav underline)
- Links: 0.2s ease (color change)

---

## Usage Guidelines

### When to Use Each Color

**Code (Deep Blue):**
- Technical projects
- Architecture/systems posts
- Software engineering content
- Database and backend work

**AI (Purple):**
- Machine learning projects
- AI research and experiments
- AI learning journey posts
- Data science content

**Fitness (Orange):**
- Health and fitness projects
- Workout tracking systems
- Nutrition and wellness content
- Physical training posts

**Meta (Cyan):**
- Philosophy and reflection
- Habit stacking and discipline
- Personal development
- Vitruvian Project content

**Synergy (Gradient):**
- Hero sections
- Section dividers
- Content bridging multiple disciplines
- Featured/highlighted content

---

## Brand Voice Through Design

The visual system should communicate:
- **Discipline:** Clean, organized, purposeful design
- **Excellence:** Polished, attention to detail
- **Integration:** Visual connections between elements
- **Authenticity:** Personality in color and presentation
- **Growth:** Progressive enhancement and evolution

---

## Future Enhancements

1. **Custom Typography:** Implement geometric or tech-forward custom font family
2. **Animated Transitions:** SVG animations showing interconnected systems
3. **Interactive Elements:** Hover effects revealing discipline connections
4. **Dark Mode:** Full dark theme with adjusted color palette
5. **Icons:** Custom icon set reflecting synergy theme
6. **Illustrations:** Original artwork showing discipline intersections

---

## CSS Variable Reference

All design system colors, gradients, and sizes are defined as CSS variables for easy updates:

```css
:root {
    --primary-color: #1a237e;
    --secondary-color: #422c4d;
    --accent-color: #ff8a3d;
    --color-code: #1a237e;
    --color-ai: #7c3aed;
    --color-fitness: #ff8a3d;
    --color-meta: #06b6d4;
    /* ... plus gradients and shadows */
}
```

Update these variables to instantly change the entire site's visual identity.

---

## Implementation Checklist

- [x] Color palette defined
- [x] Typography system established
- [x] Discipline tags created
- [x] Utility classes implemented
- [x] Design system JavaScript created
- [ ] Update navbar with new colors
- [ ] Refresh hero section design
- [ ] Apply discipline tags to blog posts
- [ ] Color-code projects by discipline
- [ ] Update card designs throughout
- [ ] Test responsive design
- [ ] Implement interactive features
