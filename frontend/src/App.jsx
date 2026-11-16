import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import Chatbot from './pages/Chatbot';
import Yoga from './pages/Yoga';
import Diet from './pages/Diet';
import Movies from './pages/Movies';

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/chatbot" element={<Chatbot />} />
        <Route path="/yoga" element={<Yoga />} />
        <Route path="/diet" element={<Diet />} />
        <Route path="/movies" element={<Movies />} />
      </Routes>
    </Layout>
  );
}
