const API = process.env.REACT_APP_API_URL;

export const getPosts = async (filter) => {
  let url = `${API}/posts`;
  if (filter) url += `?sentiment=${filter}`;
  const res = await fetch(url);
  return res.json();
};

export const createPost = async (formData) => {
  const res = await fetch(`${API}/posts`, {
    method: 'POST',
    body: formData,
  });
  return res.json();
};

export const getDashboardData = async () => {
  const res = await fetch(`${API}/dashboard`);
  return res.json();
};
