import React from 'react';

const colorMap = {
  Positive: 'green',
  Neutral: 'gold',
  Negative: 'red',
};

const SentimentBadge = ({ label }) => (
  <span className="sentiment-badge" style={{ background: colorMap[label] || 'gray' }}>
    {label}
  </span>
);

export default SentimentBadge;
