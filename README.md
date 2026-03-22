# TradingDashboard

A comprehensive Portfolio Analytics and Trading Dashboard. This project provides a full-stack solution for monitoring stock portfolios, analyzing concentration risks, and managing trading settings.

## Features

- **Portfolio Overiew**: Track total investment, current value, and overall P&L.
- **Concentration Analytics**: Visualize asset allocation and monitor concentration limits across different sectors/groups.
- **Dynamic Grouping**: Custom grouping for Stocks.
- **Exit Engine**: (Planned/In Development) Tools to assist in managing exit strategies.
- **Fragility & Diversification Engine**: (Planned/In Development) Tools to assist in managing diversification strategies.
- **Kite Connect Integration**: Live data integration with Zerodha's Kite Connect API.

## Project Structure

- `backend/`: FastAPI application handling data processing, settings persistence (SQLite), and external API integrations.
- `frontend/`: React application built with Vite and Tailwind CSS for a modern, responsive user interface.

## Prerequisites

- [Python 3.10+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/)
- [Kite Connect API Key & Secret](https://kite.trade/)

## Setup and Installation

### Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables in `.env`:
   ```env
   KITE_API_KEY=your_api_key
   KITE_API_SECRET=your_api_secret
   REDIRECT_URL=your_redirect_url
   ```
5. Run the server:
   ```bash
   python main.py
   ```

### Frontend

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```