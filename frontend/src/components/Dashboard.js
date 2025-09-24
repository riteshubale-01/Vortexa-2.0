import React, { useEffect, useState } from 'react';
import { getDashboardData } from '../api';
import { Pie, Line } from 'react-chartjs-2';

const Dashboard = () => {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 5000); // Poll every 5s
    return () => clearInterval(interval);
  }, []);

  const fetchDashboard = async () => {
    const res = await getDashboardData();
    setData(res);
  };

  if (!data) return <div>Loading dashboard...</div>;

  return (
    <div>
      <h2>Sentiment Over Time</h2>
      <Line data={data.lineChart} />
      <h2>Sentiment Distribution</h2>
      <Pie data={data.pieChart} />
      <h2>Top Keywords</h2>
      <ul>
        {Object.entries(data.topKeywords).map(([sentiment, keywords]) => (
          <li key={sentiment}>
            <b>{sentiment}:</b> {keywords.join(', ')}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Dashboard;
