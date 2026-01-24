import React from 'react';
import TradingChart from './components/TradingChart';
import OrderBook from './components/OrderBook';
import PositionManager from './components/PositionManager';
import PerformanceMetrics from './components/PerformanceMetrics';

const App = () => (
  <div>
    <h1>Gold Trading Bot Dashboard</h1>
    <TradingChart />
    <OrderBook />
    <PositionManager />
    <PerformanceMetrics />
  </div>
);

export default App;
