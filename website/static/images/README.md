# Website Images Directory

This directory contains all images used throughout the website, organized by purpose.

## Directory Structure

```
images/
├── profile/          # Profile and personal photos
│   └── me.jpg       # Profile photo (used in About Me section)
├── portfolio/       # Portfolio project images and screenshots
└── projects/        # Individual project images and assets
```

## Guidelines

### Profile Images
- **Location**: `profile/`
- **Purpose**: Personal photos for About Me section and author bio
- **Recommended Size**: 350px width (responsive, scales to 280px on mobile)
- **Format**: JPEG or PNG
- **Naming**: `me.jpg`, `profile-photo.jpg`, etc.

### Portfolio Images
- **Location**: `portfolio/`
- **Purpose**: Project screenshots and feature images for portfolio cards
- **Recommended Size**: 400-600px width
- **Format**: PNG (for better quality) or JPEG
- **Naming**: `{project-name}-{description}.png`

### Project Images
- **Location**: `projects/`
- **Purpose**: Content images for individual project pages
- **Recommended Size**: Flexible based on layout
- **Format**: PNG or JPEG
- **Naming**: Descriptive names related to the project

## CSS Classes for Images

### Profile Image
```html
<img src="/static/images/profile/me.jpg" alt="Nathan Bowman" class="profile-image">
```
- Styling: Rounded corners, shadow effect, hover elevation

### Portfolio Images (Future Use)
Add classes as needed:
- `.portfolio-image`: For portfolio section images
- `.project-image`: For project-specific content images

## Image Optimization Tips

1. Use appropriate formats:
   - JPEG for photographs
   - PNG for graphics with transparency
   - WebP for modern browsers (with fallback)

2. Optimize file sizes:
   - Compress before uploading
   - Consider tools like TinyPNG or ImageOptim

3. Use responsive images:
   - Set max-width in CSS
   - Use srcset for different screen sizes (future enhancement)

4. Always include alt text for accessibility
