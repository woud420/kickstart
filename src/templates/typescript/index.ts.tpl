import express, { Request, Response } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

const app = express();

// Middleware
app.use(helmet());
app.use(cors());
app.use(morgan('combined'));
app.use(express.json());

// Types
interface HealthResponse {
  status: string;
  service: string;
  version: string;
  timestamp: string;
}

interface RootResponse {
  message: string;
}

// Routes
app.get('/', (req: Request, res: Response<RootResponse>) => {
  res.json({
    message: '{{SERVICE_NAME}} is running'
  });
});

app.get('/health', (req: Request, res: Response<HealthResponse>) => {
  res.json({
    status: 'healthy',
    service: '{{SERVICE_NAME}}',
    version: '0.1.0',
    timestamp: new Date().toISOString()
  });
});

// Configuration
const HOST = process.env.HOST || '0.0.0.0';
const PORT = parseInt(process.env.PORT || '8000', 10);

// Start server
app.listen(PORT, HOST, () => {
  console.log(`{{SERVICE_NAME}} server running on http://${HOST}:${PORT}`);
});

export default app;
