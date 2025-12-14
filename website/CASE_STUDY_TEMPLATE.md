# Case Study Template Documentation

## Overview

The case study template (`case_study.html`) is a professional, magazine-style page for showcasing project details and impact. It's designed to tell compelling stories about your work while maintaining consistent branding with "The Vitruvian Developer" theme.

## Features

### 1. Professional Layout
- **Hero Section**: Eye-catching header with project title, discipline tags, and quick metadata
- **Sidebar Navigation**: Sticky sidebar with quick facts, technologies, and disciplines
- **Magazine-Style Content**: Clean, readable article layout with visual hierarchy
- **Responsive Design**: Adapts beautifully from desktop to mobile

### 2. Key Sections
The template includes comprehensive sections for:
- **The Problem**: What challenge does your project solve?
- **The Solution**: How did you approach it?
- **Technologies & Tools**: Technologies used with detailed listings
- **My Role & Contributions**: What did you build/contribute?
- **Challenges & Solutions**: Obstacles encountered and how you overcame them
- **Results & Impact**: Quantifiable outcomes and achievements
- **Key Learnings**: What you learned from the project
- **Links & Resources**: Links to GitHub, live demos, documentation, etc.

### 3. Design Elements
- Discipline-colored badges (Code, AI, Fitness, Meta)
- Gradient backgrounds reflecting brand colors
- Sticky sidebar for consistent information access
- Smooth hover effects and transitions
- Print-friendly styling

## How to Use

### 1. Update Project Summary File

Each project needs a `_project_summary.md` file in its root directory with YAML front matter. Example:

```markdown
---
title: "AI-Powered Health Dashboard"
tagline: "Real-time biometric tracking with machine learning predictions"
disciplines:
  - code
  - ai
  - fitness
role: "Lead Developer & Data Engineer"
timeline: "6 months (Mar - Aug 2024)"
status: "Active"
quick_facts:
  - "100,000+ users"
  - "Real-time processing"
  - "99.9% uptime"

technologies:
  - Python
  - TensorFlow
  - FastAPI
  - PostgreSQL
  - React
  - Docker

problem: |
  Traditional health tracking apps are reactive—they collect data but don't predict outcomes.
  Users have no way to understand their trajectory or get proactive insights about their health risks.

  The healthcare industry needed a solution that combines real-time biometric collection with predictive
  analytics to enable preventive health decisions.

solution: |
  Built an end-to-end AI platform that:
  - Ingests real-time biometric data from wearables and smart health devices
  - Uses machine learning to predict health trends 30 days in advance
  - Provides personalized recommendations based on individual risk profiles
  - Integrates with existing healthcare provider systems

contributions:
  - Architected the end-to-end data pipeline for biometric ingestion and processing
  - Designed and trained 3 custom ML models for health prediction
  - Built the FastAPI backend serving 100+ requests per second
  - Led integration with partner healthcare systems
  - Mentored 2 junior engineers on ML best practices

challenges:
  - challenge: "Real-time processing at scale"
    solution: "Implemented stream processing with Apache Kafka and optimized database indexing to handle peak loads"
  - challenge: "Model accuracy with limited training data"
    solution: "Used transfer learning from public health datasets and domain-expert annotation"
  - challenge: "Privacy compliance (HIPAA)"
    solution: "Implemented encryption at rest/transit and role-based access controls"

results:
  - metric: "Prediction Accuracy"
    value: "87%"
  - metric: "User Retention"
    value: "78%"
  - metric: "Time to Prediction"
    value: "< 50ms"
  - "Reduced hospital readmission rates by 15% among pilot users"
  - "Generated $2.3M in annual revenue"

learnings:
  - Healthcare products require deep regulatory understanding—invest early in compliance
  - Real-time ML systems need different architecture than batch processing
  - User trust is critical; transparency in predictions is non-negotiable
  - Building with domain experts from day one prevents costly redesigns

links:
  GitHub:
    description: "Source code and model implementations"
    url: "https://github.com/nbowman189/health-ai-platform"
  Live Demo:
    description: "Live dashboard demonstration"
    url: "https://health-demo.example.com"
  Article:
    description: "Technical deep dive on the ML architecture"
    url: "/blog/ai-health-predictions-architecture"
  Documentation:
    description: "Complete API and integration guide"
    url: "https://docs.example.com/health-ai"
---

# Additional Content

You can add additional markdown content here that will be rendered in the case study.
This content will appear after the structured sections above.

## Why This Approach Worked

The integration of machine learning with domain expertise proved to be the winning formula...

```

### 2. YAML Front Matter Fields

#### Required Fields
- **title** (string): Project name/title
- **disciplines** (array): One or more of: `code`, `ai`, `fitness`, `meta`

#### Optional Fields
- **tagline** (string): Short description of the project
- **role** (string): Your role on the project
- **timeline** (string): Project duration
- **status** (string): Current status (Active, Completed, Paused, etc.)
- **quick_facts** (array): Key stats or facts displayed in hero
- **technologies** (array): Tech stack used
- **problem** (string): Markdown-formatted problem statement
- **solution** (string): Markdown-formatted solution description
- **contributions** (array): List of your contributions
- **challenges** (array): Either simple strings or objects with `challenge` and `solution` keys
- **results** (array): Mix of strings and objects with `metric` and `value` fields
- **learnings** (array): Key takeaways from the project
- **links** (object): Links section with structure:
  ```yaml
  links:
    GitHub:
      description: "Source code"
      url: "https://..."
    Live Demo:
      description: "Live version"
      url: "https://..."
  ```

### 3. Access the Case Study

Once the `_project_summary.md` file is created, access it at:

```
/project-case-study/{project-name}
```

Examples:
- `/project-case-study/Health_and_Fitness`
- `/project-case-study/AI_Development`

## Design System Integration

The template automatically applies the project's discipline colors:

| Discipline | Color | Use Case |
|-----------|-------|----------|
| Code | Deep Navy (#1a237e) | Software engineering, systems work |
| AI | Slate Blue (#6a5acd) | Machine learning, data science |
| Fitness | Amber (#ffb347) | Health, fitness, physical projects |
| Meta | Cyan (#06b6d4) | Philosophy, reflection, personal growth |

## Customization

### Color Scheme
The template uses CSS variables from the design system. To modify colors:
1. Edit `/static/css/style.css`
2. Update the CSS variables in `:root`
3. Changes automatically apply site-wide

### Styling
The template includes comprehensive CSS for:
- Hero section gradient backgrounds
- Sidebar styling with accent borders
- Section dividers
- Link cards
- Responsive breakpoints

All styling is contained within the `<style>` block in `case_study.html` for easy customization.

### Custom Content Sections
To add custom sections:
1. Add a section in the template:
```html
<section id="custom-section" class="cs-section">
    <h2>Custom Title</h2>
    <div id="custom-content">Loading...</div>
</section>
```

2. Update the JavaScript to populate it from metadata:
```javascript
if (metadata.custom_field) {
    document.getElementById('custom-content').innerHTML = metadata.custom_field;
}
```

## API Integration

The template automatically fetches case study data from:

```
GET /api/project/{project_name}/summary
```

This endpoint returns:
```json
{
    "title": "Project name",
    "metadata": {
        "title": "...",
        "disciplines": [...],
        "problem": "...",
        "solution": "...",
        ...
    },
    "content": "Raw markdown",
    "html": "Rendered HTML"
}
```

The JavaScript in the template parses this data and populates all sections automatically.

## Mobile Responsiveness

The template is fully responsive with breakpoints at:
- **1024px**: Sidebar converts to grid layout below content
- **768px**: Adjusted typography and spacing
- **640px**: Single-column layout, optimized touch targets

## Accessibility

- Semantic HTML5 structure
- Proper heading hierarchy (h1 → h6)
- Breadcrumb navigation for context
- ARIA labels on interactive elements
- Print-friendly styles for easy sharing

## Examples

### Example 1: Simple Project
Minimal case study with just the essential information.

### Example 2: Complex Project
Full case study with detailed technical information, metrics, and learnings.

### Example 3: Synergy Project
Project spanning multiple disciplines (Code + AI + Fitness) with discipline tags in hero.

## Best Practices

1. **Problem & Solution**: Lead with the problem, then show how you solved it
2. **Metrics**: Use quantifiable results when possible (percentages, time improvements, user counts)
3. **Challenges**: Be honest about obstacles—this builds credibility
4. **Learnings**: Reflect on what you'd do differently; shows growth mindset
5. **Images**: Consider adding case study images in the markdown content for visual interest
6. **Links**: Always include links to live demos and source code

## Testing

1. **Content Testing**:
   - Verify all metadata displays correctly
   - Check that markdown renders properly
   - Test links and external resources

2. **Visual Testing**:
   - Test responsive design at mobile, tablet, desktop
   - Verify color contrast for accessibility
   - Check print styles

3. **Performance**:
   - Monitor initial load time
   - Ensure images are optimized
   - Test with slow network conditions

## Troubleshooting

### Metadata not displaying
- Check that `_project_summary.md` exists in project root
- Verify YAML front matter is properly formatted
- Check browser console for API errors

### Styling issues
- Clear browser cache (Cmd+Shift+R on Mac)
- Verify CSS variables are defined in `:root`
- Check for CSS selector conflicts

### Links not working
- Verify URLs in YAML are complete (include https://)
- Check that external links open in new tabs
- Test internal links are relative to site root

## Future Enhancements

Potential improvements:
- [ ] Video embeds in hero section
- [ ] Timeline visualization for project timeline
- [ ] Related projects carousel
- [ ] Comments/feedback section
- [ ] Export to PDF functionality
- [ ] Social media sharing buttons
- [ ] Dark mode support

## Support

For issues or questions:
1. Check the API response: `/api/project/{name}/summary`
2. Review YAML formatting in `_project_summary.md`
3. Consult the design system documentation
4. Check browser console for JavaScript errors
