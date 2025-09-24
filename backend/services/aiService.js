const { Configuration, OpenAIApi } = require('openai');
const configuration = new Configuration({ apiKey: process.env.OPENAI_API_KEY });
const openai = new OpenAIApi(configuration);

// Classify sentiment using OpenAI
exports.classifySentiment = async (text) => {
  // Prompt for sentiment classification
  const prompt = `Classify the sentiment of this post as Positive, Neutral, or Negative. \nGive a confidence score (0-1) and a one-line explanation. \nFormat: {"sentiment_label": "...", "confidence": 0.0, "explanation": "..."}\n\nPost: ${text}`;

  const response = await openai.createChatCompletion({
    model: 'gpt-3.5-turbo',
    messages: [{ role: 'user', content: prompt }],
    max_tokens: 100,
    temperature: 0.2,
  });

  // Parse response
  try {
    const json = JSON.parse(response.data.choices[0].message.content);
    return json;
  } catch {
    return { sentiment_label: 'Neutral', confidence: 0.5, explanation: 'Could not determine.' };
  }
};
