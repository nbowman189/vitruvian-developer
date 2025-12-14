# Private Workspace Server Setup

## Current Implementation (Option 1: Simple Local-Only Server)

Your private workspace server is configured to run on **port 8081** (separate from the public server on 8080).

### Running Both Servers

```bash
# Terminal 1: Public portfolio server
cd /Users/nathanbowman/primary-assistant/website
python app.py

# Terminal 2: Private workspace server
cd /Users/nathanbowman/primary-assistant/website
python app-private.py
```

Access:
- **Public Portfolio**: http://localhost:8080
- **Private Workspace**: http://localhost:8081

### Key Differences from Public Server

| Feature | Public (app.py) | Private (app-private.py) |
|---------|-----------------|--------------------------|
| Port | 8080 | 8081 |
| Access | Portfolio only | All project files |
| Data files | ✗ Blocked | ✓ Full access |
| Working logs | ✗ Blocked | ✓ Full access |
| Coaching notes | ✗ Blocked | ✓ Full access |
| Authentication | None needed | None (local-only) |

### File Structure Access

**Public Server (app.py):**
- `project_dir/docs/*.md` only
- `project_dir/GEMINI.md` only

**Private Server (app-private.py):**
- `project_dir/docs/*.md` (all files)
- `project_dir/data/*.md` (working files)
- `project_dir/GEMINI.md`

---

## Future Upgrade Options

When you're ready to add authentication or expose this privately to other devices, here are your upgrade paths:

### Option 2: Basic Authentication (Lightweight)

Add HTTP Basic Auth or session-based login to the existing server.

**Pros:**
- Simple to implement (~50 lines of code)
- Can stay on same port or separate port
- Works well for single-user access
- No database needed

**Cons:**
- Password in environment variable or config file
- Not suitable for multiple users
- Should use HTTPS if exposed externally

**Implementation:**
```python
# Add to app-private.py
from flask import request
from functools import wraps
import os

PASSWORD = os.getenv('PRIVATE_WORKSPACE_PASSWORD', 'default-change-me')

def check_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.password != PASSWORD:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Apply to all routes:
@app.route('/api/...')
@check_auth
def protected_route():
    ...
```

**Setup:**
```bash
PRIVATE_WORKSPACE_PASSWORD=your-secure-password python app-private.py
```

### Option 3: Session-Based Login (Medium)

Add a login page with session management.

**Pros:**
- User-friendly login interface
- Session-based access (no password in every request)
- Can support multiple users with different permissions
- Cleaner than HTTP Basic Auth

**Cons:**
- Requires session management library (flask-session)
- Slightly more complex (~150 lines)
- Should use HTTPS if exposed externally

**Dependencies:**
```bash
pip install flask-session
```

**Implementation Structure:**
```python
from flask_session import Session
from flask import session, redirect, url_for

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Check password
    # Set session['authenticated'] = True

@app.route('/logout')
def logout():
    # Clear session

def require_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated
```

### Option 4: Production-Ready OAuth/JWT (Advanced)

For secure external access with proper authentication.

**Pros:**
- Industry-standard security
- Can support mobile access
- Better audit trails
- Scalable to multiple devices/users

**Cons:**
- More complex setup (~300-500 lines)
- Requires database for sessions
- SSL/TLS certificate needed
- Overkill for single-user local access

**Dependencies:**
```bash
pip install flask-jwt-extended python-dotenv
```

**Architecture:**
- JWT tokens for stateless authentication
- Refresh tokens for long-lived sessions
- HTTPS required
- Database for token blacklisting (optional)

---

## Recommendation for Next Steps

1. **Immediate**: Use current setup (Option 1)
   - Keep both servers running during development
   - Private server handles your working files
   - Zero security overhead for local-only access

2. **When sharing with others or accessing from mobile**: Upgrade to Option 2
   - Add password protection
   - Simple environment variable setup
   - 15 minutes to implement

3. **If you want a polished UI**: Add Option 3
   - Login page on private server
   - Better user experience
   - Still simple implementation

4. **Only if deploying publicly**: Use Option 4
   - Full OAuth/JWT implementation
   - Production-grade security
   - External access support

---

## Migration Path

All three upgrade options are compatible with the current file structure:

```
website/
├── app.py                    # Public portfolio
├── app-private.py            # Private workspace (current)
├── app-auth.py              # (Future) Option 2: Basic auth version
├── app-sessions.py          # (Future) Option 3: Session-based version
├── app-production.py        # (Future) Option 4: JWT/OAuth version
└── PRIVATE_SERVER_SETUP.md   # This file
```

To upgrade:
1. Create new `app-{variant}.py` file
2. Run alongside existing servers
3. Test at different port
4. Switch over when ready
5. Keep old version as backup

---

## Environment Variables

For current setup:
```bash
# Optional - control which port private server runs on
FLASK_PORT=8081           # Default: 8081
FLASK_HOST=127.0.0.1      # Default: 127.0.0.1 (localhost only)
FLASK_DEBUG=False         # Default: False (set to True for development)
```

For Option 2+ upgrades:
```bash
PRIVATE_WORKSPACE_PASSWORD=your-secure-password  # Option 2+
FLASK_SECRET_KEY=your-secret-key                 # Option 3+
```

---

## Security Notes

### Current Setup (Local-Only)
- ✓ Zero security risk (localhost only)
- ✓ No password needed
- ✓ Perfect for personal development
- ✗ Only accessible from this machine
- ✗ Not suitable for external access

### Before External Exposure
- Add password protection (Option 2 minimum)
- Use HTTPS/SSL certificate
- Restrict to VPN or private network
- Consider firewall rules
- Enable CSRF protection
- Add rate limiting

---

## Troubleshooting

### Port already in use
```bash
# Find what's using port 8081
lsof -i :8081

# Kill the process
kill -9 <PID>

# Or use different port
FLASK_PORT=8082 python app-private.py
```

### File not found errors on private server
- Make sure `utils/file_utils.py` has `allow_data_access=True` parameter
- Check that data directory exists: `Health_and_Fitness/data/`
- Verify file permissions

### Can't connect to server
- Make sure FLASK_HOST is not restricted to specific interface
- Try `FLASK_HOST=0.0.0.0` to bind all interfaces (less secure)
- Check firewall settings

---

## Related Files

- `app.py` - Public portfolio server
- `app-private.py` - Private workspace server (current)
- `utils/file_utils.py` - File access utilities
- `CLAUDE.md` - Main project documentation
