const mongoose = require('mongoose');

const PostSchema = new mongoose.Schema({
  post_id: { type: String, unique: true },
  user: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
  title: String,
  body: String,
  media_urls: [String],
  timestamp: { type: Date, default: Date.now },
  sentiment_label: String,
  confidence: Number,
  explanation: String,
  isAIDailyNews: { type: Boolean, default: false },
  source: { type: String, default: 'user' }, // 'user', 'reddit', 'twitter', 'ainews'
});

module.exports = mongoose.model('Post', PostSchema);
