const Post = require('../models/Post');
const { classifySentiment } = require('../services/aiService');
const { moderateContent } = require('../services/moderationService');
const { v4: uuidv4 } = require('uuid');
const path = require('path');
const fs = require('fs');

// Create a new post
exports.createPost = async (req, res) => {
  try {
    const { title, body, userId } = req.body;
    const files = req.files || [];
    if (files.length > 7) return res.status(400).json({ error: 'Max 7 files allowed.' });

    // Moderation
    const modResult = await moderateContent(title + ' ' + body);
    if (!modResult.allowed) {
      return res.status(400).json({ error: 'Content violates rules: ' + modResult.reason });
    }

    // Sentiment
    const sentiment = await classifySentiment(title + ' ' + body);

    // Save files
    const media_urls = files.map(file => '/uploads/' + file.filename);

    const post = new Post({
      post_id: uuidv4(),
      user: userId,
      title,
      body,
      media_urls,
      ...sentiment,
    });
    await post.save();

    // Notify via WebSocket
    const { broadcastNewPost } = require('../utils/websocket');
    broadcastNewPost(post);

    res.status(201).json(post);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};

// Get posts (with optional sentiment filter)
exports.getPosts = async (req, res) => {
  try {
    const { sentiment, following, userId } = req.query;
    let filter = {};
    if (sentiment) filter.sentiment_label = sentiment;
    if (following && userId) {
      // Only posts from followed users
      const user = await require('../models/User').findById(userId);
      filter.user = { $in: user.following };
    }
    const posts = await Post.find(filter).sort({ timestamp: -1 }).populate('user', 'username');
    res.json(posts);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};
