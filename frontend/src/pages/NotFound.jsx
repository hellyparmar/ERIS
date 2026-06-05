import React from 'react';
import { Link } from 'react-router-dom';
import { LayoutDashboard } from 'lucide-react';

const NotFound = () => (
  <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4 py-10">
    <div className="w-full max-w-3xl rounded-[28px] border border-slate-200 bg-white p-10 shadow-xl">
      <div className="text-center">
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">404 — Page Not Found</p>
        <h1 className="mt-6 text-5xl font-semibold tracking-tight text-slate-900 sm:text-6xl">We can’t find that page.</h1>
        <p className="mt-4 text-base leading-7 text-slate-600 sm:text-lg">
          The page you are looking for does not exist or may have moved. Please check the URL or return to your dashboard.
        </p>

        <div className="mt-8 flex justify-center">
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 rounded-2xl bg-slate-900 px-6 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
          >
            <LayoutDashboard className="h-4 w-4" />
            Go to Dashboard
          </Link>
        </div>
      </div>
    </div>
  </div>
);

export default NotFound;
