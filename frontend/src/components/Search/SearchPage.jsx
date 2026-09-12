import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { searchDrugs } from '../../services/api';
import './SearchPage.css';

function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  async function handleSearch(e) {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError('');
    setResults(null);

    try {
      const data = await searchDrugs(query.trim());
      setResults(data);
    } catch (err) {
      setError(err.message || 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  const brands = results?.brands ?? [];
  const generics = results?.generics ?? [];
  const substances = results?.substances ?? [];
  const hasResults = brands.length > 0 || generics.length > 0 || substances.length > 0;

  return (
    <div className="search-page">
      <div className="search-card">
        <h1 className="search-heading">Search Drugs</h1>

        <form className="search-form" onSubmit={handleSearch}>
          <input
            id="drug-search-input"
            type="text"
            className="search-input"
            placeholder="Enter drug name, brand, or substance…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Drug search"
          />
          <button
            id="drug-search-btn"
            type="submit"
            className="search-btn"
            disabled={loading}
          >
            {loading ? 'Searching…' : 'Search'}
          </button>
        </form>

        {error && (
          <p className="search-error" role="alert">{error}</p>
        )}

        {results !== null && !loading && (
          <div className="search-results">
            {!hasResults ? (
              <p className="no-results">No drugs found.</p>
            ) : (
              <>
                {/* Brands Section */}
                {brands.length > 0 && (
                  <section className="results-section">
                    <h2 className="section-heading">Brands</h2>
                    <ul className="results-list">
                      {brands.map((item) => (
                        <li key={item.identifier} className="result-item result-item--brand">
                          <div className="result-info">
                            <span className="result-primary">{item.identifier}</span>
                            <span className="result-secondary">{item.brand_name}</span>
                          </div>
                          <button
                            className="btn-alternatives"
                            onClick={() => navigate(`/results/${encodeURIComponent(item.identifier)}`)}
                          >
                            Find Alternatives
                          </button>
                        </li>
                      ))}
                    </ul>
                  </section>
                )}

                {/* Generics Section */}
                {generics.length > 0 && (
                  <section className="results-section">
                    <h2 className="section-heading">Generics</h2>
                    <ul className="results-list">
                      {generics.map((item) => (
                        <li key={item.identifier} className="result-item result-item--generic">
                          <div className="result-info">
                            <span className="result-primary">{item.identifier}</span>
                            <span className="result-secondary">{item.generic_name}</span>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </section>
                )}

                {/* Substances Section */}
                {substances.length > 0 && (
                  <section className="results-section">
                    <h2 className="section-heading">Substances</h2>
                    <ul className="results-list">
                      {substances.map((item) => (
                        <li key={item.identifier} className="result-item">
                          <span className="result-primary">{item.substance_name}</span>
                        </li>
                      ))}
                    </ul>
                  </section>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default SearchPage;
