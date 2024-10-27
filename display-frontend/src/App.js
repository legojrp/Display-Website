import React from 'react';
import { Helmet } from 'react-helmet';
import Display from './screens/Display';

function App() {
  return (
    <>
      <Helmet>
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <title>Your App Title</title>
      </Helmet>
      <Display />
    </>
  );
}

export default App;
