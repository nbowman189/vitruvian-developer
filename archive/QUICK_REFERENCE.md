# Quick Reference Guide

## 🚀 Start Website
```bash
cd /Users/nathanbowman/primary-assistant/website
python app.py
```
Opens at: `http://localhost:8080`

## 📁 Key Directories
```
/website                          # Flask app
├── app.py                        # Main application
├── templates/                    # HTML templates
├── static/
│   ├── css/style.css            # All styling
│   ├── js/                      # JavaScript
│   └── images/branding/         # Vitruvian assets
└── blog/                        # Blog posts

/AI_Development/                 # Project markdown files
/Health_and_Fitness/             # Health data & files
/scripts/                        # Data processing utilities
```

## 📄 Documentation Files
| File | Purpose |
|------|---------|
| **WEBSITE_STATUS_SUMMARY.md** | Current website status & features |
| **SESSION_WRAP_UP.md** | This session's work summary |
| **VITRUVIAN_BRANDING_IMPLEMENTATION.md** | Branding integration details |
| **IMPLEMENTATION_COMPLETE.md** | Technical overhaul documentation |
| **PROJECT_IMPLEMENTATION_PLAN.md** | Implementation phases & roadmap |
| **project-pages-ux-analysis.md** | UX/accessibility analysis |
| **brand portfolio review Claude.md** | Brand positioning review |
| **CLAUDE.md** | Project overview & architecture |

## 🎨 Brand Assets Location
All Vitruvian Man images in: `/website/static/images/branding/`

| File | Size | Use |
|------|------|-----|
| favicon.ico | 0.5KB | Browser tabs |
| vitruvian-hero.jpg | 208KB | Hero background |
| vitruvian-about.jpg | 46KB | About section |
| vitruvian-social.jpg | 71KB | Social base |
| linkedin-banner.jpg | 83KB | LinkedIn |
| twitter-header.jpg | 82KB | Twitter |

## 🔧 Common Development Tasks

### Update Hero Section
Edit: `website/static/css/style.css` (line 743)

### Update About Section
Edit: `website/templates/index.html` (lines 51-71)

### Add Blog Post
1. Create `website/blog/slug-name.md`
2. Include YAML front matter:
```yaml
---
title: Post Title
date: 2025-11-18
tags: [tag1, tag2]
excerpt: Short description
---
```

### Update Project Metadata
Edit: `website/app.py` - `PROJECT_METADATA` dictionary

## 🔗 Important URLs

**Local Development:**
- Homepage: `http://localhost:8080/`
- Blog: `http://localhost:8080/blog`
- Graphs: `http://localhost:8080/health-and-fitness/graphs`

**API Endpoints:**
- Projects: `http://localhost:8080/api/projects`
- Metadata: `http://localhost:8080/api/projects-metadata`
- Blog posts: `http://localhost:8080/api/blog/posts`

## 💾 Quick Commits
```bash
cd /Users/nathanbowman/primary-assistant
git add .
git commit -m "Update website content"
```

## 🧪 Testing Checklist
Before deployment:
- [ ] Check homepage layout on mobile (devtools)
- [ ] Verify all images load (no 404s)
- [ ] Test project navigation
- [ ] Check blog post rendering
- [ ] Verify favicon visible
- [ ] Test contact links

## 📱 Responsive Breakpoints
- Desktop: 1200px+
- Tablet: 768px - 1200px
- Mobile: Below 768px

## 🎯 Next Steps (Choose One)

**Quick Wins** (1-2 hours):
- Deploy to production
- Update LinkedIn with banner
- Upload Twitter header

**Content Growth** (3-5 hours):
- Write blog posts
- Create case studies
- Expand descriptions

**Strategic** (5+ hours):
- Newsletter setup
- Email marketing
- Content calendar

## 📞 Support
For detailed information, refer to the comprehensive documentation files listed above.

---
**Last Updated:** November 18, 2025
**Status:** Production Ready ✅
