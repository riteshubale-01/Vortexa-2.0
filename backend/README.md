# Backend Setup

## Prerequisites
- Node.js v18+
- MongoDB (local or Atlas)
- OpenAI API Key (or HuggingFace)
- (Optional) SendGrid or Gmail for emails

## Setup

1. `cp .env.example .env` and fill in your secrets.
2. `npm install`
3. `npm start`

## Endpoints
- `POST /api/posts` — create post & classify sentiment
- `GET /api/posts` — fetch all posts (filter by sentiment)
- `GET /api/dashboard` — fetch dashboard data
- `POST /api/follow` — follow/unfollow users
- WebSocket endpoint for live updates

## Notes
- File uploads use `/uploads` folder (auto-created).
- AI Daily News is posted every 12 hours (cron).
- Trending posts are ingested from Reddit/X.
- Content moderation blocks abusive posts.
