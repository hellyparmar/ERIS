import React, { useEffect, useRef } from 'react';
import { Chart as ChartJS } from 'chart.js';

/**
 * ChartWrapper component to properly manage Chart.js lifecycle
 * This ensures charts are destroyed before being recreated, preventing canvas reuse errors
 */
const ChartWrapper = ({ children, chartId }) => {
    const containerRef = useRef(null);

    useEffect(() => {
        // Cleanup function to destroy all chart instances in this container
        return () => {
            if (containerRef.current) {
                const canvas = containerRef.current.querySelector('canvas');
                if (canvas) {
                    const chartInstance = ChartJS.getChart(canvas);
                    if (chartInstance) {
                        chartInstance.destroy();
                    }
                }
            }
        };
    }, []);

    return (
        <div ref={containerRef} key={chartId}>
            {children}
        </div>
    );
};

export default ChartWrapper;
