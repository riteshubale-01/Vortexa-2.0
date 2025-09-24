// Express server with WebSocket, file upload, and scheduled AI news
const express = require('express');
const http = require('http');
const cors = require('cors');
const mongoose = require('mongoose');
const dotenv = require('dotenv');
const { setupWebSocket } = require('./utils/websocket');
const postRoutes = require('./routes/postRoutes');
const userRoutes = require('./routes/userRoutes');
const dashboardRoutes = require('./routes/dashboardRoutes');
const aiNewsRoutes = require('./routes/aiNewsRoutes');
const cron = require('node-cron');

dotenv.config();

const app = express();
const server = http.createServer(app);

setupWebSocket(server);

app.use(cors());
app.use(express.json());
app.use('/uploads', express.static('uploads'));

app.use('/api/posts', postRoutes);
app.use('/api/users', userRoutes);
app.use('/api/dashboard', dashboardRoutes);
app.use('/api/ainews', aiNewsRoutes);

mongoose.connect(process.env.MONGODB_URI)
  .then(() => console.log('MongoDB connected'))
  .catch(err => console.error(err));

// Schedule AI Daily News every 12 hours
const { postAIDailyNews } = require('./controllers/aiNewsController');
cron.schedule('0 */12 * * *', postAIDailyNews);

const PORT = process.env.PORT || 5000;
server.listen(PORT, () => console.log(`Server running on port ${PORT}`));
