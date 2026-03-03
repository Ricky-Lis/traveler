import React, { useState } from 'react';
import { motion } from 'motion/react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { authService } from '@/services/authService';
import { Loader2, Plane, Compass } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    // Clear any existing tokens to prevent interference
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');

    try {
      const response = await authService.login({ email, password });
      const { access_token, user } = response.data;
      
      // Store token and user info
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('user', JSON.stringify(user));
      
      // Redirect or update state (for now just alert success)
      alert(`欢迎回来, ${user.nickname || '旅行者'}!`);
      
    } catch (err: any) {
      console.error('Login failed:', err);
      if (err.response) {
        console.error('Error response data:', err.response.data);
        
        // 后端 401 统一返回 { "detail": "错误描述" }
        if (err.response.status === 401) {
          setError(err.response.data?.detail || '邮箱或密码错误。如果您还没有账号，请先注册。');
        } else {
          const errorMessage = err.response.data?.detail || 
                               err.response.data?.message || 
                               '登录失败，请检查您的凭据。';
          setError(errorMessage);
        }
      } else if (err.request) {
        console.error('Error request:', err.request);
        setError('服务器无响应，请检查网络连接。');
      } else {
        console.error('Error message:', err.message);
        setError(`请求错误: ${err.message}`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-black font-sans text-white">
      {/* Background Image with Overlay */}
      <div 
        className="absolute inset-0 z-0 bg-cover bg-center bg-no-repeat opacity-60"
        style={{ backgroundImage: 'url("https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?q=80&w=2021&auto=format&fit=crop")' }}
      />
      <div className="absolute inset-0 z-0 bg-gradient-to-b from-black/30 via-black/60 to-black/90" />

      {/* Content */}
      <div className="relative z-10 flex min-h-screen flex-col items-center justify-center px-6 py-12">
        
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="mb-12 text-center"
        >
          <div className="mb-4 flex justify-center space-x-2 text-white/80">
            <Plane className="h-6 w-6" />
            <Compass className="h-6 w-6" />
          </div>
          <h1 className="font-serif text-5xl font-light tracking-tight text-white md:text-7xl">
            Traveler
          </h1>
          <p className="mt-4 text-lg font-light text-white/70">
            探索世界，开启您的旅程。
          </p>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
          className="w-full max-w-sm space-y-6"
        >
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-2">
              <Input
                type="email"
                placeholder="邮箱地址"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="bg-white/5 border-white/10 text-white placeholder:text-white/40 focus:border-white/30 focus:bg-white/10"
              />
            </div>
            <div className="space-y-2">
              <Input
                type="password"
                placeholder="密码"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="bg-white/5 border-white/10 text-white placeholder:text-white/40 focus:border-white/30 focus:bg-white/10"
              />
            </div>

            {error && (
              <div className="rounded-md bg-red-500/10 p-3 text-sm text-red-200 border border-red-500/20">
                {error}
              </div>
            )}

            <Button 
              type="submit" 
              className="w-full bg-white text-black hover:bg-white/90 h-12 text-base font-medium tracking-wide"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  登录中...
                </>
              ) : (
                '登录'
              )}
            </Button>
          </form>

          <div className="text-center text-sm text-white/50 space-y-4">
            <div>
              <button 
                type="button"
                onClick={() => navigate('/forgot-password')}
                className="text-white/70 hover:text-white hover:underline underline-offset-4 text-xs"
              >
                忘记密码？
              </button>
            </div>
            <div>
              <p>还没有账号？</p>
              <button 
                type="button"
                onClick={() => navigate('/register')}
                className="mt-2 text-white hover:underline underline-offset-4 font-medium"
              >
                注册新账号
              </button>
            </div>
          </div>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 0.8 }}
          className="absolute bottom-8 left-0 right-0 flex justify-center space-x-6 text-xs text-white/30 uppercase tracking-widest"
        >
          <span>探索</span>
          <span>•</span>
          <span>连接</span>
          <span>•</span>
          <span>分享</span>
        </motion.div>
      </div>
    </div>
  );
}
