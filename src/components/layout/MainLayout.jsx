/**
 * Enterprise Retail Intelligence System v3.0
 * LAYOUT - MAIN LAYOUT
 * 
 * Primary layout structure with Sidebar and Header
 * V3.0 Standard: Presentation vs Container pattern
 */

import Header from './Header';
import Sidebar from './Sidebar';

const MainLayout = ({ children, currentView = 'dashboard' }) => {
    return (
        <div className="flex h-screen bg-gray-50 dark:bg-gray-950">
            {/* Sidebar */}
            <Sidebar currentView={currentView} />

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col overflow-hidden">
                {/* Header */}
                <Header />

                {/* Content */}
                <main className="flex-1 overflow-y-auto custom-scrollbar p-6">
                    {children}
                </main>
            </div>
        </div>
    );
};

export default MainLayout;
