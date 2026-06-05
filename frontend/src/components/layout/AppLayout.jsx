import Sidebar from './Sidebar';
import Header from './Header';
import './app-layout.css';

export default function AppLayout({ children, pageTitle = 'Dashboard' }) {
  return (
    <div className="app-layout">
      <Sidebar />
      <div className="app-main">
        <Header pageTitle={pageTitle} />
        <main className="app-content">
          {children}
        </main>
      </div>
    </div>
  );
}
