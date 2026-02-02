import React, { useState, useEffect, useRef } from 'react';

/**
 * LazyImage Component
 * Lazy loads images with intersection observer
 * Supports WebP with fallback to original format
 */
export const LazyImage = ({
    src,
    alt,
    className = '',
    width,
    height,
    placeholder = 'blur',
    onLoad,
    ...props
}) => {
    const [isLoaded, setIsLoaded] = useState(false);
    const [isInView, setIsInView] = useState(false);
    const imgRef = useRef(null);

    useEffect(() => {
        if (!imgRef.current) return;

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        setIsInView(true);
                        observer.disconnect();
                    }
                });
            },
            {
                rootMargin: '50px', // Start loading 50px before entering viewport
            }
        );

        observer.observe(imgRef.current);

        return () => {
            if (imgRef.current) {
                observer.unobserve(imgRef.current);
            }
        };
    }, []);

    const handleLoad = () => {
        setIsLoaded(true);
        if (onLoad) onLoad();
    };

    // Generate WebP source if supported
    const webpSrc = src?.replace(/\.(jpg|jpeg|png)$/i, '.webp');
    const shouldUseWebP = src && src.match(/\.(jpg|jpeg|png)$/i);

    return (
        <div
            ref={imgRef}
            className={`lazy-image-container ${className}`}
            style={{
                position: 'relative',
                overflow: 'hidden',
                width: width || '100%',
                height: height || 'auto',
            }}
        >
            {/* Placeholder */}
            {!isLoaded && placeholder === 'blur' && (
                <div
                    className="lazy-image-placeholder"
                    style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        height: '100%',
                        backgroundColor: '#f0f0f0',
                        filter: 'blur(10px)',
                        transform: 'scale(1.1)',
                    }}
                />
            )}

            {/* Actual Image */}
            {isInView && (
                <picture>
                    {shouldUseWebP && (
                        <source srcSet={webpSrc} type="image/webp" />
                    )}
                    <img
                        src={src}
                        alt={alt}
                        loading="lazy"
                        onLoad={handleLoad}
                        style={{
                            opacity: isLoaded ? 1 : 0,
                            transition: 'opacity 0.3s ease-in-out',
                            width: '100%',
                            height: '100%',
                            objectFit: 'cover',
                        }}
                        {...props}
                    />
                </picture>
            )}
        </div>
    );
};

/**
 * Responsive Image Component
 * Provides different image sizes for different screen sizes
 */
export const ResponsiveImage = ({
    src,
    alt,
    sizes = {
        mobile: 640,
        tablet: 768,
        desktop: 1024,
        wide: 1920,
    },
    className = '',
    ...props
}) => {
    const generateSrcSet = () => {
        const basePath = src.replace(/\.[^.]+$/, '');
        const ext = src.match(/\.[^.]+$/)?.[0] || '.jpg';

        return Object.entries(sizes)
            .map(([_, width]) => `${basePath}-${width}w${ext} ${width}w`)
            .join(', ');
    };

    const generateSizes = () => {
        return `
      (max-width: 640px) 640px,
      (max-width: 768px) 768px,
      (max-width: 1024px) 1024px,
      1920px
    `;
    };

    return (
        <LazyImage
            src={src}
            alt={alt}
            srcSet={generateSrcSet()}
            sizes={generateSizes()}
            className={className}
            {...props}
        />
    );
};

/**
 * Background Image Component
 * Lazy loads background images
 */
export const LazyBackgroundImage = ({
    src,
    children,
    className = '',
    style = {},
    ...props
}) => {
    const [isLoaded, setIsLoaded] = useState(false);
    const [isInView, setIsInView] = useState(false);
    const divRef = useRef(null);

    useEffect(() => {
        if (!divRef.current) return;

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        setIsInView(true);
                        observer.disconnect();
                    }
                });
            },
            {
                rootMargin: '50px',
            }
        );

        observer.observe(divRef.current);

        return () => {
            if (divRef.current) {
                observer.unobserve(divRef.current);
            }
        };
    }, []);

    useEffect(() => {
        if (!isInView) return;

        const img = new Image();
        img.src = src;
        img.onload = () => setIsLoaded(true);
    }, [isInView, src]);

    return (
        <div
            ref={divRef}
            className={className}
            style={{
                ...style,
                backgroundImage: isLoaded ? `url(${src})` : 'none',
                backgroundColor: isLoaded ? 'transparent' : '#f0f0f0',
                transition: 'background-color 0.3s ease-in-out',
            }}
            {...props}
        >
            {children}
        </div>
    );
};

export default LazyImage;
