const { Configuration, OpenAIApi } = require('openai');
const configuration = new Configuration({ apiKey: process.env.OPENAI_API_KEY });
const openai = new OpenAIApi(configuration);

exports.moderateContent = async (text) => {
  const prompt = `Is the following post abusive, vulgar, or sensitive? \nIf yes, reply: {"allowed": false, "reason": "..."} \nIf no, reply: {"allowed": true}\n\nPost: ${text}`;

  const response = await openai.createChatCompletion({
    model: 'gpt-3.5-turbo',
    messages: [{ role: 'user', content: prompt }],
    max_tokens: 60,
    temperature: 0,
  });

  try {
    return JSON.parse(response.data.choices[0].message.content);
  } catch {
    return { allowed: true };
  }
};
