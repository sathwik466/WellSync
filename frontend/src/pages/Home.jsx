import { Link } from 'react-router-dom';
import './Home.css';

const features = [
  {
    path: '/chatbot',
    icon: '💬',
    title: 'Wellness Chatbot',
    description: 'AI-powered mental wellness assistant with knowledge base and conversation memory.',
  },
  {
    path: '/yoga',
    icon: '🧘',
    title: 'Yoga Pose Detection',
    description: 'Real-time pose correction using MoveNet with visual alignment guides.',
  },
  {
    path: '/diet',
    icon: '🥗',
    title: 'Personalized Diet Plans',
    description: 'Custom meal plans and recipes based on your preferences and ingredients.',
  },
  {
    path: '/movies',
    icon: '🎬',
    title: 'Mood-Based Movies',
    description: 'Face mood detection with curated movie recommendations.',
  },
];

export default function Home() {
  return (
    <div className="home">
      <section className="hero">
        <h1 className="hero-title">Welcome to WellSync</h1>
        <p className="hero-subtitle">
          Your all-in-one platform for mental wellness, physical fitness, nutrition, and entertainment.
        </p>
      </section>

      <section className="features-grid">
        {features.map((feature) => (
          <Link key={feature.path} to={feature.path} className="feature-card card">
            <span className="feature-icon">{feature.icon}</span>
            <h2>{feature.title}</h2>
            <p>{feature.description}</p>
            <span className="feature-link">Explore &rarr;</span>
          </Link>
        ))}
      </section>
    </div>
  );
}
