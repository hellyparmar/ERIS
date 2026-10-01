import { Helmet } from 'react-helmet-async';

const defaultTitle = 'ERIS — Enterprise Retail Intelligence System';
const defaultDesc = 'Retail analytics, measured ML forecasting, a grounded AI assistant, and GST reporting for multi-outlet operations.';

export default function SEO({
  title,
  description = defaultDesc,
  image = '/og-image.png',
  type = 'website',
}) {
  const pageTitle = title ? `${title} — ERIS` : defaultTitle;

  return (
    <Helmet>
      <title>{pageTitle}</title>
      <meta name="description" content={description} />
      <meta property="og:title" content={pageTitle} />
      <meta property="og:description" content={description} />
      <meta property="og:type" content={type} />
      <meta property="og:image" content={image} />
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={pageTitle} />
      <meta name="twitter:description" content={description} />
    </Helmet>
  );
}
