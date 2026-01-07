import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import Login from './Login'; // Corrected Import Case

function App() {
  // Persistence: Check Local Storage on load
  const [user, setUser] = useState(localStorage.getItem('recipe_user') || null);
  
  const [profile, setProfile] = useState({ 
    allergens: '', 
    calorie_limit: 500, 
    cuisine_pref: 'Any', 
    cooking_time: 30 
  });
  
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [awaitingFollowUp, setAwaitingFollowUp] = useState(false);
  const [activeTab, setActiveTab] = useState('chat'); 

  // Wrapper to save login state
  const handleLogin = (username) => {
    localStorage.setItem('recipe_user', username);
    setUser(username);
  };

  // Wrapper to clear login state
  const handleLogout = () => {
    localStorage.removeItem('recipe_user');
    setUser(null);
    setMessages([]);
  };

  useEffect(() => {
    if (user) {
      fetch(`http://127.0.0.1:5000/profile/${user}`)
        .then(res => res.json())
        .then(data => {
          if (!data.error) setProfile(data);
        })
        .catch(err => console.error("Failed to load profile", err));
    }
  }, [user]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = { role: "user", parts: [{ text: input }] };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    try {
      const historyForApi = messages.map(m => ({
        role: m.role,
        parts: m.parts
      }));

      const response = await fetch('http://127.0.0.1:5002/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input,
          history: historyForApi,
          profile: {
            calorie_limit: profile.calorie_limit,
            allergens: profile.allergens.split(',').map(s => s.trim()),
            cuisine_pref: profile.cuisine_pref
          }
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Handle streaming response
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let aiText = "";

      // Create a placeholder for the streaming message
      const streamingMsg = { role: "model", parts: [{ text: "" }] };
      setMessages([...newMessages, streamingMsg]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.trim()) {
            try {
              const json = JSON.parse(line);
              if (json.text) {
                aiText += json.text;
                // Update the streaming message with accumulated text
                setMessages(prev => {
                  const updated = [...prev];
                  updated[updated.length - 1] = {
                    role: "model",
                    parts: [{ text: aiText }]
                  };
                  return updated;
                });
              }
            } catch (e) {
              console.warn("Failed to parse JSON:", line);
            }
          }
        }
      }

      // Final update to turn off streaming
      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "model",
          parts: [{ text: aiText }]
        };
        return updated;
      });
      setAwaitingFollowUp(false);

    } catch (error) {
      console.error("Frontend error:", error);
      setMessages([...newMessages, { role: "model", parts: [{ text: "Connection Error. Is Service C running?" }] }]);
      setAwaitingFollowUp(false);
    }
    setLoading(false);
  };

  const handleSaveProfile = async () => {
    await fetch(`http://127.0.0.1:5000/profile/${user}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profile),
    });
    alert("Profile Saved!");
  };

  if (!user) return <Login onLogin={handleLogin} />;

  return (
    <div className="flex h-screen bg-slate-50 font-sans text-slate-800 overflow-hidden">
      
      {/* Sidebar */}
      <div className="w-64 bg-white border-r border-slate-200 flex flex-col shadow-sm">
        <div className="p-6 border-b border-slate-100">
          <h1 className="text-xl font-bold text-emerald-700">
            SafePlate
          </h1>
          <p className="text-xs text-slate-500 mt-1">Logged in as {user}</p>
        </div>
        
        <nav className="flex-1 p-4 space-y-2">
          <button 
            onClick={() => setActiveTab('chat')}
            className={`w-full text-left px-4 py-3 rounded-lg transition font-medium ${activeTab === 'chat' ? 'bg-emerald-50 text-emerald-700' : 'hover:bg-slate-50 text-slate-600'}`}
          >
            Chat Assistant
          </button>
          <button 
            onClick={() => setActiveTab('profile')}
            className={`w-full text-left px-4 py-3 rounded-lg transition font-medium ${activeTab === 'profile' ? 'bg-emerald-50 text-emerald-700' : 'hover:bg-slate-50 text-slate-600'}`}
          >
            My Preferences
          </button>
        </nav>

        <div className="p-4 border-t border-slate-100">
          <button onClick={handleLogout} className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition">
            Sign Out
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col relative">
        
        {/* VIEW: CHAT */}
        {activeTab === 'chat' && (
          <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full h-full">
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {messages.length === 0 && (
                <div className="text-center text-slate-400 mt-20">
                  <p className="text-lg font-medium">Hello {user}</p>
                  <p className="text-sm">I'm ready to help you find safe recipes.</p>
                </div>
              )}
              
              {messages.map((msg, idx) => (
                <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[80%] rounded-2xl px-5 py-3 shadow-sm ${
                    msg.role === 'user' 
                      ? 'bg-emerald-600 text-white rounded-br-none' 
                      : 'bg-white border border-slate-200 text-slate-700 rounded-bl-none'
                  }`}>
                    <div className="prose prose-sm max-w-none dark:prose-invert leading-relaxed">
                        {msg.follow_up && (
                          <div className="mb-2 text-xs text-amber-700 font-semibold">Follow-up question — please clarify</div>
                        )}
                        <ReactMarkdown>{msg.parts[0].text}</ReactMarkdown>
                    </div>
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-slate-100 rounded-2xl px-5 py-3 text-slate-500 text-sm animate-pulse">
                    Thinking...
                  </div>
                </div>
              )}
            </div>

            <div className="p-4 bg-white border-t border-slate-200">
              <form onSubmit={handleSend} className="flex gap-4">
                <input 
                  type="text" 
                  className="flex-1 p-4 border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none shadow-sm transition"
                  placeholder={awaitingFollowUp ? "Please clarify the question above (e.g., 'tree nuts only' or 'seeds included')" : "Ask for a recipe..."}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  disabled={loading}
                />
                <button 
                  type="submit" 
                  disabled={loading}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-2 rounded-xl font-bold shadow-md transition disabled:opacity-50"
                >
                  Send
                </button>
              </form>
            </div>
          </div>
        )}

        {/* VIEW: PROFILE */}
        {activeTab === 'profile' && (
          <div className="flex-1 p-10 overflow-y-auto">
            <div className="max-w-2xl mx-auto bg-white p-8 rounded-xl shadow-sm border border-slate-200">
              <h2 className="text-2xl font-bold mb-6 text-slate-800">Your Safe Profile</h2>
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Allergens</label>
                  <input 
                    type="text" 
                    className="w-full p-3 border border-slate-300 rounded-lg focus:ring-emerald-500"
                    value={profile.allergens}
                    onChange={e => setProfile({...profile, allergens: e.target.value})}
                    placeholder="e.g. peanuts, shellfish"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-bold text-slate-700 mb-2">Calorie Limit</label>
                    <input 
                      type="number" 
                      className="w-full p-3 border border-slate-300 rounded-lg"
                      value={profile.calorie_limit}
                      onChange={e => setProfile({...profile, calorie_limit: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-slate-700 mb-2">Preferred Cuisine</label>
                    <select 
                      className="w-full p-3 border border-slate-300 rounded-lg"
                      value={profile.cuisine_pref}
                      onChange={e => setProfile({...profile, cuisine_pref: e.target.value})}
                    >
                      {['Any', 'Italian', 'Mexican', 'Asian', 'Indian'].map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </div>
                </div>
                <button onClick={handleSaveProfile} className="w-full bg-slate-900 text-white py-3 rounded-lg font-bold hover:bg-slate-800 transition">Save Changes</button>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

export default App;