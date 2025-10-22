@echo off
echo Syncing DB-Buddy Security Updates to Repository...

cd /d "c:\Users\thiagarajan.b\OneDrive - IDP Education Ltd\D drive files\IDP\Personal (1)\tb-repo-git\DB-Buddy"

echo Adding new security files...
git add vector_security.py
git add misinformation_validator.py
git add consumption_limiter.py
git add VECTOR_SECURITY_IMPLEMENTATION.md

echo Adding updated application files...
git add streamlit_app.py
git add app.py
git add security_validator.py

echo Committing security enhancements...
git commit -m "feat: Implement comprehensive OWASP LLM Top 10 security measures

- Add vector and embedding security validation (LLM11)
- Implement misinformation and hallucination detection
- Add unbounded consumption protection with rate limiting
- Enhance input/output validation and sanitization
- Add overreliance prevention with user education
- Integrate security measures across Streamlit and Flask apps
- Add comprehensive monitoring and logging
- Include usage statistics and circuit breaker protection"

echo Pushing to repository...
git push origin main

echo Security updates synchronized successfully!
pause