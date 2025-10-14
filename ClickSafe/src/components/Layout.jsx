import Navigation from './Navigation';

const Layout = ({ children }) => {
  return (
    <div className="min-h-screen w-full">
      <Navigation />
      <main className="w-full">
        {children}
      </main>
    </div>
  );
};

export default Layout;
