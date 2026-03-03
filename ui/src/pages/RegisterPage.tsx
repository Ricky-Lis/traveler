import React, { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Loader2, ArrowLeft, Mail, Lock, User, KeyRound } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { authService } from '@/services/authService';

export default function RegisterPage() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [isSendingCode, setIsSendingCode] = useState(false);
  const [cooldown, setCooldown] = useState(0);
  
  const [formData, setFormData] = useState({
    email: '',
    code: '',
    password: '',
    nickname: ''
  });
  
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (cooldown > 0) {
      timer = setInterval(() => {
        setCooldown((prev) => prev - 1);
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [cooldown]);

  const handleSendCode = async () => {
    if (!formData.email) {
      setError('请先输入您的邮箱');
      return;
    }
    
    setIsSendingCode(true);
    setError(null);
    
    try {
      await authService.sendCode(formData.email);
      setCooldown(60);
      alert('验证码已发送至您的邮箱！');
    } catch (err: any) {
      console.error('Send code failed:', err);
      setError(err.response?.data?.detail || '发送验证码失败');
    } finally {
      setIsSendingCode(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const response = await authService.register({
        email: formData.email,
        code: formData.code,
        password: formData.password,
        nickname: formData.nickname || undefined
      });

      const { access_token, user } = response.data;
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('user', JSON.stringify(user));
      
      alert(`欢迎, ${user.nickname}! 注册成功。`);
      navigate('/'); // Redirect to home/dashboard (which is currently login, but effectively logged in)
      
    } catch (err: any) {
      console.error('Registration failed:', err);
      setError(err.response?.data?.detail || '注册失败，请重试。');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-black font-sans text-white">
      {/* Background Image with Overlay */}
      <div 
        className="absolute inset-0 z-0 bg-cover bg-center bg-no-repeat opacity-60"
        style={{ backgroundImage: 'url("https://images.unsplash.com/photo-1501785888041-af3ef285b470?q=80&w=2070&auto=format&fit=crop")' }}
      />
      <div className="absolute inset-0 z-0 bg-gradient-to-b from-black/30 via-black/60 to-black/90" />

      {/* Content */}
      <div className="relative z-10 flex min-h-screen flex-col items-center justify-center px-6 py-12">
        
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="w-full max-w-md"
        >
          <Button 
            variant="ghost" 
            className="mb-8 pl-0 text-white/70 hover:text-white hover:bg-transparent"
            onClick={() => navigate('/login')}
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            返回登录
          </Button>

          <div className="mb-8 text-center">
            <h1 className="font-serif text-4xl font-light tracking-tight text-white">
              创建账号
            </h1>
            <p className="mt-2 text-white/60">
              加入我们，开启您的旅程。
            </p>
          </div>

          <form onSubmit={handleRegister} className="space-y-4">
            {/* Email Field with Send Code Button */}
            <div className="space-y-2">
              <div className="relative flex gap-2">
                <div className="relative flex-1">
                  <Mail className="absolute left-3 top-3 h-5 w-5 text-white/40" />
                  <Input
                    type="email"
                    placeholder="邮箱地址"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    required
                    className="pl-10 bg-white/5 border-white/10 text-white placeholder:text-white/40 focus:border-white/30 focus:bg-white/10"
                  />
                </div>
                <Button
                  type="button"
                  onClick={handleSendCode}
                  disabled={isSendingCode || cooldown > 0 || !formData.email}
                  className="w-32 bg-white/10 hover:bg-white/20 text-white border border-white/20"
                >
                  {isSendingCode ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : cooldown > 0 ? (
                    `${cooldown}秒`
                  ) : (
                    '发送验证码'
                  )}
                </Button>
              </div>
            </div>

            {/* Verification Code */}
            <div className="space-y-2">
              <div className="relative">
                <KeyRound className="absolute left-3 top-3 h-5 w-5 text-white/40" />
                <Input
                  type="text"
                  placeholder="验证码 (6位数字)"
                  value={formData.code}
                  onChange={(e) => setFormData({...formData, code: e.target.value})}
                  required
                  maxLength={6}
                  className="pl-10 bg-white/5 border-white/10 text-white placeholder:text-white/40 focus:border-white/30 focus:bg-white/10 tracking-widest"
                />
              </div>
            </div>

            {/* Password */}
            <div className="space-y-2">
              <div className="relative">
                <Lock className="absolute left-3 top-3 h-5 w-5 text-white/40" />
                <Input
                  type="password"
                  placeholder="密码 (至少6位)"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  required
                  minLength={6}
                  className="pl-10 bg-white/5 border-white/10 text-white placeholder:text-white/40 focus:border-white/30 focus:bg-white/10"
                />
              </div>
            </div>

            {/* Nickname */}
            <div className="space-y-2">
              <div className="relative">
                <User className="absolute left-3 top-3 h-5 w-5 text-white/40" />
                <Input
                  type="text"
                  placeholder="昵称 (选填)"
                  value={formData.nickname}
                  onChange={(e) => setFormData({...formData, nickname: e.target.value})}
                  className="pl-10 bg-white/5 border-white/10 text-white placeholder:text-white/40 focus:border-white/30 focus:bg-white/10"
                />
              </div>
            </div>

            {error && (
              <div className="rounded-md bg-red-500/10 p-3 text-sm text-red-200 border border-red-500/20 text-center">
                {error}
              </div>
            )}

            <Button 
              type="submit" 
              className="w-full bg-white text-black hover:bg-white/90 h-12 text-base font-medium tracking-wide mt-6"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  注册中...
                </>
              ) : (
                '注册'
              )}
            </Button>
          </form>
        </motion.div>
      </div>
    </div>
  );
}
