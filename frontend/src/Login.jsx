import { useState } from 'react';

function Login({ onLogin }) {
  const [view, setView] = useState('login'); // 'login', 'register', 'forgot', 'reset'
  const [formData, setFormData] = useState({
    username: '', email: '', password: '', code: '', newPassword: ''
  });
  const [msg, setMsg] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMsg('');
    
    const endpoint = view === 'register' ? '/register' : '/login';
    
    try {
      const res = await fetch(`http://127.0.0.1:5000${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      const data = await res.json();
      
      if (res.ok) {
        if (view === 'register') {
          setMsg("Account created! Please log in.");
          setView('login');
        } else {
          onLogin(formData.username);
        }
      } else {
        setMsg(`${data.error}`);
      }
    } catch (err) { setMsg("Connection failed."); }
    setLoading(false);
  };

  const handleForgot = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:5000/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: formData.email }),
      });
      const data = await res.json();
      if (res.ok) {
        setMsg("Code sent! Check your email.");
        setView('reset');
      } else {
        setMsg(`${data.error}`);
      }
    } catch (err) { setMsg("Connection failed."); }
    setLoading(false);
  };

  const handleReset = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:5000/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          email: formData.email, 
          code: formData.code, 
          new_password: formData.newPassword 
        }),
      });
      if (res.ok) {
        setMsg("Password reset! Please log in.");
        setView('login');
      } else {
        const data = await res.json();
        setMsg(`${data.error}`);
      }
    } catch (err) { setMsg("Connection failed."); }
    setLoading(false);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 font-sans">
      <div className="w-full max-w-md bg-white p-8 rounded-2xl shadow-xl border border-slate-200">
        <h2 className="text-3xl font-extrabold text-center text-emerald-600 mb-6">SafePlate</h2>
        <h3 className="text-xl font-bold mb-4 text-gray-800 border-b pb-2">
          {view === 'login' && 'Log In'}
          {view === 'register' && 'Sign Up'}
          {view === 'forgot' && 'Reset Password'}
          {view === 'reset' && 'Enter Code'}
        </h3>

        {/* LOGIN */}
        {view === 'login' && (
          <form onSubmit={handleAuth} className="space-y-4">
            <input name="username" placeholder="Username" onChange={handleChange} className="w-full p-3 border rounded-lg" required />
            <input name="password" type="password" placeholder="Password" onChange={handleChange} className="w-full p-3 border rounded-lg" required />
            <div className="text-right">
              <button type="button" onClick={() => setView('forgot')} className="text-sm text-emerald-600 hover:underline">Forgot Password?</button>
            </div>
            <button type="submit" disabled={loading} className="w-full py-3 bg-emerald-600 text-white font-bold rounded-lg hover:bg-emerald-700">{loading ? '...' : 'Log In'}</button>
            <p className="text-center text-sm text-gray-600 mt-4">
              New? <button type="button" onClick={() => setView('register')} className="text-emerald-600 font-bold hover:underline">Create Account</button>
            </p>
          </form>
        )}

        {/* REGISTER */}
        {view === 'register' && (
          <form onSubmit={handleAuth} className="space-y-4">
            <input name="username" placeholder="Choose Username" onChange={handleChange} className="w-full p-3 border rounded-lg" required />
            <input name="email" type="email" placeholder="Email Address" onChange={handleChange} className="w-full p-3 border rounded-lg" required />
            <input name="password" type="password" placeholder="Password" onChange={handleChange} className="w-full p-3 border rounded-lg" required />
            <button type="submit" disabled={loading} className="w-full py-3 bg-emerald-600 text-white font-bold rounded-lg hover:bg-emerald-700">{loading ? '...' : 'Sign Up'}</button>
            <p className="text-center text-sm text-gray-600 mt-4">
              <button type="button" onClick={() => setView('login')} className="text-gray-500 hover:underline">Back to Login</button>
            </p>
          </form>
        )}

        {/* FORGOT PASSWORD */}
        {view === 'forgot' && (
          <form onSubmit={handleForgot} className="space-y-4">
            <p className="text-sm text-gray-600">Enter your email to receive a reset code.</p>
            <input name="email" type="email" placeholder="Email Address" onChange={handleChange} className="w-full p-3 border rounded-lg" required />
            <button type="submit" disabled={loading} className="w-full py-3 bg-slate-800 text-white font-bold rounded-lg hover:bg-black">{loading ? 'Sending...' : 'Send Code'}</button>
            <p className="text-center text-sm mt-4"><button type="button" onClick={() => setView('login')} className="text-gray-500 hover:underline">Cancel</button></p>
          </form>
        )}

        {/* RESET CODE */}
        {view === 'reset' && (
          <form onSubmit={handleReset} className="space-y-4">
            <p className="text-sm text-gray-600">Check your email ({formData.email}) for the code.</p>
            <input name="code" placeholder="6-Digit Code" onChange={handleChange} className="w-full p-3 border rounded-lg" required />
            <input name="newPassword" type="password" placeholder="New Password" onChange={handleChange} className="w-full p-3 border rounded-lg" required />
            <button type="submit" disabled={loading} className="w-full py-3 bg-red-600 text-white font-bold rounded-lg hover:bg-red-700">{loading ? 'Updating...' : 'Set New Password'}</button>
          </form>
        )}

        {msg && <div className="mt-4 p-3 bg-gray-100 text-center text-sm rounded-lg font-medium">{msg}</div>}
      </div>
    </div>
  );
}

export default Login;