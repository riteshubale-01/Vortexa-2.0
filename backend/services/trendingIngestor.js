// Ingest trending posts from Reddit/X (pseudo-code, use APIs or RSS in production)
const Post = require('../models/Post');
const { classifySentiment } = require('./aiService');
const axios = require('axios');

exports.ingestTrending = async () => {
  // Example: fetch Reddit hot posts (replace with real API)
  const res = await axios.get('https://www.reddit.com/r/worldnews/hot.json?limit=5');
  for (const item of res.data.data.children) {
    const postData = item.data;
    const sentiment = await classifySentiment(postData.title + ' ' + postData.selftext);
    const post = new Post({
      post_id: postData.id,
      user: null,
      title: postData.title,
      body: postData.selftext,
      media_urls: [],
      ...sentiment,
      source: 'reddit',
    });
    await post.save();
  }
};
