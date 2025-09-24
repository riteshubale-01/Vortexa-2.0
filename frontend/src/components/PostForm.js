import React, { useState } from 'react';
import { createPost } from '../api';

const PostForm = ({ userId }) => {
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [files, setFiles] = useState([]);
  const [error, setError] = useState(null);

  const handleSubmit = async e => {
    e.preventDefault();
    if (files.length > 7) {
      setError('Max 7 files allowed.');
      return;
    }
    const formData = new FormData();
    formData.append('title', title);
    formData.append('body', body);
    formData.append('userId', userId);
    for (let file of files) formData.append('media', file);
    const res = await createPost(formData);
    if (res.error) setError(res.error);
    else {
      setTitle('');
      setBody('');
      setFiles([]);
      setError(null);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="post-form">
      <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Title" required />
      <textarea value={body} onChange={e => setBody(e.target.value)} placeholder="Body" required />
      <input type="file" multiple accept="image/*,video/*,audio/*" onChange={e => setFiles([...e.target.files])} />
      {error && <div className="error">{error}</div>}
      <button type="submit">Post</button>
    </form>
  );
};

export default PostForm;
