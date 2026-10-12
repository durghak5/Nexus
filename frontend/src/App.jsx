import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar/Navbar';
import SearchPage from './components/Search/SearchPage';
import UploadPage from './components/Upload/UploadPage';
import ResultsPage from './components/Results/ResultsPage';
import ChatPage from './components/Chat/ChatPage';

function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <main style={{ padding: '2rem' }}>
        <Routes>
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/" element={<SearchPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/results/:brandName" element={<ResultsPage />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}

export default App;