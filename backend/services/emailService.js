const nodemailer = require('nodemailer');
const { Configuration, OpenAIApi } = require('openai');
const configuration = new Configuration({ apiKey: process.env.OPENAI_API_KEY });
const openai = new OpenAIApi(configuration);

const transporter = nodemailer.createTransport({
  service: 'gmail',
  auth: {
    user: process.env.EMAIL_USER,
    pass: process.env.EMAIL_PASS,
  },
});

exports.sendWelcomeEmail = async (to, username) => {
  // Generate AI welcome message
  const prompt = `Write a friendly, one-paragraph welcome email for a new user named ${username} joining a Reddit-like social app.`;
  const response = await openai.createChatCompletion({
    model: 'gpt-3.5-turbo',
    messages: [{ role: 'user', content: prompt }],
    max_tokens: 100,
    temperature: 0.7,
  });
  const message = response.data.choices[0].message.content;

  await transporter.sendMail({
    from: process.env.EMAIL_USER,
    to,
    subject: 'Welcome to Vortexa!',
    text: message,
  });
};
