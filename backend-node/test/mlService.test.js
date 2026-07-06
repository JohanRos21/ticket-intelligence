const test = require('node:test');
const assert = require('node:assert/strict');

process.env.ML_SERVICE_URL = 'http://ml.test:8001';
process.env.ML_TIMEOUT_MS = '100';

const { predictTicket } = require('../src/services/mlService');

test.afterEach(() => {
  delete global.fetch;
});

test('predictTicket normaliza una respuesta exitosa', async () => {
  global.fetch = async (url, options) => {
    assert.equal(url, 'http://ml.test:8001/predict');
    assert.equal(options.method, 'POST');
    assert.deepEqual(JSON.parse(options.body), {
      title: 'No puedo entrar',
      description: 'Olvidé mi clave',
    });
    return {
      ok: true,
      json: async () => ({
        category: 'acceso_autenticacion',
        confidence: 0.91,
        model_version: 'tfidf_logreg_v0.1',
      }),
    };
  };

  const result = await predictTicket({
    title: 'No puedo entrar',
    description: 'Olvidé mi clave',
  });

  assert.deepEqual(result, {
    success: true,
    predictionStatus: 'predicted',
    category: 'acceso_autenticacion',
    confidence: 0.91,
    modelVersion: 'tfidf_logreg_v0.1',
  });
});

test('predictTicket degrada con seguridad ante un error HTTP', async () => {
  global.fetch = async () => ({
    ok: false,
    status: 503,
    text: async () => 'no disponible',
  });

  const result = await predictTicket({ title: 'Ticket', description: '' });

  assert.equal(result.success, false);
  assert.equal(result.predictionStatus, 'failed');
  assert.match(result.error, /503/);
});

test('predictTicket degrada con seguridad ante un error de red', async () => {
  global.fetch = async () => {
    throw new Error('connection refused');
  };

  const result = await predictTicket({ title: 'Ticket', description: '' });

  assert.deepEqual(result, {
    success: false,
    predictionStatus: 'unavailable',
    error: 'connection refused',
  });
});
