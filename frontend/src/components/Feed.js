import React, { useEffect, useState } from 'react';
import SentimentBadge from './SentimentBadge';
import MediaViewer from './MediaViewer';
import Notification from './Notification';
import { getPosts } from '../api';

const Feed = ({ filter }) => {
  const [posts, setPosts] = useState([]);
  const [notif, setNotif] = useState(null);

  useEffect(() => {
    fetchPosts();
    // WebSocket for live updates
    const ws = new WebSocket('ws://localhost:5000');
    ws.onmessage = (msg) => {
      const data = JSON.parse(msg.data);
      if (data.type === 'new_post') {
        setNotif('New post added!');
        setTimeout(() => setNotif(null), 2000);
        fetchPosts();
      }
    };
    return () => ws.close();
  }, [filter]);

  const fetchPosts = async () => {
    const res = await getPosts(filter);
    setPosts(res);
  };

  return (
    <div>
      {notif && <Notification message={notif} />}
      {posts.map(post => (
        <div className="post" key={post.post_id}>
          <div className="post-header">
            <span className="username">{post.user?.username || post.source}</span>
            <span className="timestamp">{new Date(post.timestamp).toLocaleString()}</span>
            <SentimentBadge label={post.sentiment_label} />
          </div>
          <h3>{post.title}</h3>
          <p>{post.body}</p>
          <MediaViewer media={post.media_urls} />
          <div className="explanation">{post.explanation}</div>
        </div>
      ))}
    </div>
  );
};

export default Feed;
