# Meeting AI — Sample Demo Scenarios & cURL API Collection

### 1. Register User
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Abhishek R", "email": "abhishek@meetingai.com", "password": "securepassword123"}'
```

### 2. Login & Get Access Token
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "abhishek@meetingai.com", "password": "securepassword123"}'
```

### 3. Create Meeting
```bash
curl -X POST http://localhost:8000/api/v1/meetings \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Weekly Backend Sync", "description": "Reviewing API deadlines and Docker deployment", "language": "en"}'
```

### 4. Upload Audio Recording
```bash
curl -X POST http://localhost:8000/api/v1/meetings/<MEETING_ID>/upload \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F "file=@weekly-sync.mp3"
```

### 5. Trigger Multi-Stage AI Pipeline
```bash
curl -X POST http://localhost:8000/api/v1/meetings/<MEETING_ID>/process \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### 6. Check Real-Time Processing Progress
```bash
curl -X GET http://localhost:8000/api/v1/meetings/<MEETING_ID>/processing-status \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### 7. Retrieve Structured Transcript & Speakers
```bash
curl -X GET http://localhost:8000/api/v1/meetings/<MEETING_ID>/transcript \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### 8. View Executive & Detailed AI Summary
```bash
curl -X GET http://localhost:8000/api/v1/meetings/<MEETING_ID>/summary \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### 9. View Extracted Action Items & Decisions
```bash
curl -X GET http://localhost:8000/api/v1/meetings/<MEETING_ID>/action-items \
  -H "Authorization: Bearer <ACCESS_TOKEN>"

curl -X GET http://localhost:8000/api/v1/meetings/<MEETING_ID>/decisions \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### 10. Cross-Meeting Full-Text Search
```bash
curl -X GET "http://localhost:8000/api/v1/search/meetings?q=Docker" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```
