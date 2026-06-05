import React, { useEffect, useState, useRef } from 'react';

export default function WidthProvider(ComposedComponent) {
    return function WidthProvider(props) {
        const [width, setWidth] = useState(1200);
        const elementRef = useRef(null);

        useEffect(() => {
            const element = elementRef.current;
            if (!element) return;

            const resizeObserver = new ResizeObserver((entries) => {
                for (const entry of entries) {
                    setWidth(entry.contentRect.width);
                }
            });

            resizeObserver.observe(element);

            return () => {
                resizeObserver.disconnect();
            };
        }, []);

        return (
            <div ref={elementRef} className="width-provider-container w-full h-full">
                <ComposedComponent {...props} width={width} />
            </div>
        );
    };
}
