import request from 'supertest';
import app from '../src/index';

describe('{{SERVICE_NAME}} API', () => {
  describe('GET /', () => {
    it('should return the root message', async () => {
      const response = await request(app)
        .get('/')
        .expect(200);

      expect(response.body).toEqual({
        message: '{{SERVICE_NAME}} is running'
      });
    });
  });

  describe('GET /health', () => {
    it('should return health check response', async () => {
      const response = await request(app)
        .get('/health')
        .expect(200);

      expect(response.body).toMatchObject({
        status: 'healthy',
        service: '{{SERVICE_NAME}}',
        version: '0.1.0'
      });
      
      expect(response.body.timestamp).toBeDefined();
    });

    it('should have the correct response structure', async () => {
      const response = await request(app)
        .get('/health')
        .expect(200);

      const requiredFields = ['status', 'service', 'version', 'timestamp'];
      requiredFields.forEach(field => {
        expect(response.body).toHaveProperty(field);
      });
    });
  });
});