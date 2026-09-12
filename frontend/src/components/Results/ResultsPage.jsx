import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getRecommendations } from '../../services/api';
import './ResultsPage.css';

function ResultsPage() {
  const { brandName } = useParams();
  const decodedBrand = decodeURIComponent(brandName);

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    setError('');
    setData(null);

    getRecommendations(decodedBrand)
      .then((res) => setData(res))
      .catch((err) => setError(err.message || 'Failed to load recommendations.'))
      .finally(() => setLoading(false));
  }, [decodedBrand]);

  const originalPrice = data?.original_price ?? data?.price ?? null;
  const alternatives = data?.alternatives ?? data?.recommendations ?? [];

  function formatCurrency(val) {
    if (val == null) return '—';
    return `$${Number(val).toFixed(2)}`;
  }

  function calcSavings(altPrice) {
    if (originalPrice == null || altPrice == null) return null;
    return originalPrice - altPrice;
  }

  function calcSavingsPct(altPrice) {
    if (originalPrice == null || originalPrice === 0 || altPrice == null) return null;
    return ((originalPrice - altPrice) / originalPrice) * 100;
  }

  return (
    <div className="results-page">
      <div className="results-card">
        <Link to="/search" className="back-link">← Back to Search</Link>

        <h1 className="results-heading">
          Alternatives for: <span className="brand-highlight">{decodedBrand}</span>
        </h1>

        {originalPrice != null && (
          <p className="original-price">
            Original price: <strong>{formatCurrency(originalPrice)}</strong>
          </p>
        )}

        {loading && (
          <p className="results-loading">Loading recommendations…</p>
        )}

        {error && (
          <p className="results-error" role="alert">{error}</p>
        )}

        {!loading && !error && alternatives.length === 0 && (
          <p className="no-results">No alternatives found for <strong>{decodedBrand}</strong>.</p>
        )}

        {!loading && !error && alternatives.length > 0 && (
          <div className="table-wrapper">
            <table className="results-table">
              <thead>
                <tr>
                  <th>Brand Name</th>
                  <th>Price</th>
                  <th>Savings</th>
                  <th>Savings %</th>
                </tr>
              </thead>
              <tbody>
                {alternatives.map((alt, idx) => {
                  const savings = calcSavings(alt.price);
                  const savingsPct = calcSavingsPct(alt.price);
                  const isCheaper = savings != null && savings > 0;
                  const isMoreExpensive = savings != null && savings < 0;

                  return (
                    <tr key={alt.identifier ?? alt.brand_name ?? idx}>
                      <td>{alt.brand_name ?? alt.name ?? '—'}</td>
                      <td>{formatCurrency(alt.price)}</td>
                      <td className={isCheaper ? 'saving-green' : isMoreExpensive ? 'saving-gray' : ''}>
                        {savings != null
                          ? isCheaper
                            ? `Save ${formatCurrency(savings)}`
                            : isMoreExpensive
                            ? `+${formatCurrency(Math.abs(savings))}`
                            : 'Same price'
                          : '—'}
                      </td>
                      <td className={isCheaper ? 'saving-green' : isMoreExpensive ? 'saving-gray' : ''}>
                        {savingsPct != null
                          ? `${savingsPct > 0 ? '-' : '+'}${Math.abs(savingsPct).toFixed(1)}%`
                          : '—'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default ResultsPage;
