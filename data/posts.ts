/*
 * Posts define blog articles for the portfolio.  Each post is a small
 * technical essay aimed at demonstrating expertise in AI/ML engineering.
 * You can add more posts by extending the `posts` array.
 */

export interface Post {
  slug: string;
  title: string;
  summary: string;
  date: string; // ISO date string
  content: string[]; // array of paragraphs for simplicity
}

export const posts: Post[] = [
  {
    slug: 'real-time-fraud-detection-llm-ml',
    title: 'Designing a Real‑Time Fraud Detection System with LLMs',
    summary:
      'A deep dive into how we combined large language models with tabular machine learning to stop fraud without hurting customer experience.',
    date: '2025-12-10',
    content: [
      'Fraud detection at scale requires more than just predictive accuracy – it demands low latency, interpretability and continuous monitoring.  In this post I outline how we designed a hybrid system combining a Spanish language LLM with a multilayer perceptron (MLP) to analyse transfer descriptions and transaction metadata in real time.',
      'First we consolidated structured features (amount, frequency, geolocation) and unstructured text (transaction notes).  We trained a small footprint LLM to produce contextual embeddings of the descriptions.  These embeddings were concatenated with the tabular features and fed into an MLP.  Hyperparameters were tuned to balance recall and precision while keeping latency under 300 ms.',
      'We then deployed the model on AWS SageMaker with an API gateway.  A shadow deployment allowed us to compare the hybrid model against the existing tabular classifier.  Monitoring dashboards tracked latency, recall, precision and drift of both the language embeddings and tabular features.  Regular retraining ensured that vocabulary shifts and new fraud patterns were captured.',
      'The result was a 96 % recall and 84 % precision, reducing fraud losses by ~50 % without a surge in false positives.  This project showcases how modern language models can be integrated into critical financial systems when coupled with proper engineering and MLOps practices.'
    ]
  }
];