/**
 * Offline Status Indicator Component
 * Shows sync status and pending changes
 */

import React, { useState, useEffect } from 'react';
import { useOnlineStatus } from '../hooks/useOnlineStatus';
import { syncService } from '../services/syncService';
import { offlineQueue } from '../services/offlineQueue';
import './OfflineIndicator.css';

export function OfflineIndicator() {
    const isOnline = useOnlineStatus();
    const [queueStats, setQueueStats] = useState(null);
    const [syncStatus, setSyncStatus] = useState(null);
    const [storageInfo, setStorageInfo] = useState(null);
    const [showDetails, setShowDetails] = useState(false);

    // Update stats periodically
    useEffect(() => {
        const updateStats = async () => {
            const stats = await offlineQueue.getStats();
            const status = syncService.getSyncStatus();
            const storage = await syncService.getStorageInfo();

            setQueueStats(stats);
            setSyncStatus(status);
            setStorageInfo(storage);
        };

        updateStats();
        const interval = setInterval(updateStats, 10000); // Update every 10 seconds

        return () => clearInterval(interval);
    }, []);

    // Don't show if online and no pending items
    if (isOnline && queueStats?.pending === 0) {
        return null;
    }

    return (
        <div className="offline-indicator">
            <div
                className="offline-indicator-badge"
                onClick={() => setShowDetails(!showDetails)}
            >
                <div className={`status-dot ${isOnline ? 'online' : 'offline'}`} />
                <span className="status-text">
                    {isOnline ? 'Online' : 'Offline'}
                </span>
                {queueStats && queueStats.pending > 0 && (
                    <span className="pending-count">{queueStats.pending}</span>
                )}
            </div>

            {showDetails && (
                <div className="offline-indicator-details">
                    <h3>Sync Status</h3>

                    <div className="status-row">
                        <span>Connection:</span>
                        <span className={isOnline ? 'text-success' : 'text-danger'}>
                            {isOnline ? '🟢 Online' : '🔴 Offline'}
                        </span>
                    </div>

                    {syncStatus && syncStatus.last_sync_time && (
                        <div className="status-row">
                            <span>Last Sync:</span>
                            <span>{new Date(syncStatus.last_sync_time).toLocaleString()}</span>
                        </div>
                    )}

                    {queueStats && (
                        <>
                            <h4>Pending Changes</h4>
                            <div className="status-row">
                                <span>Pending:</span>
                                <span>{queueStats.pending || 0}</span>
                            </div>
                            <div className="status-row">
                                <span>Failed:</span>
                                <span className="text-danger">{queueStats.failed || 0}</span>
                            </div>
                            <div className="status-row">
                                <span>Conflicts:</span>
                                <span className="text-warning">{queueStats.conflicts || 0}</span>
                            </div>
                        </>
                    )}

                    {storageInfo && (
                        <>
                            <h4>Storage</h4>
                            <div className="status-row">
                                <span>Used:</span>
                                <span>{storageInfo.usage_mb} MB / {storageInfo.quota_mb} MB</span>
                            </div>
                            <div className="storage-bar">
                                <div
                                    className="storage-bar-fill"
                                    style={{ width: `${storageInfo.percent_used}%` }}
                                />
                            </div>
                        </>
                    )}

                    {syncStatus && syncStatus.is_syncing && (
                        <div className="sync-progress">
                            <div className="spinner" />
                            <span>Syncing...</span>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
