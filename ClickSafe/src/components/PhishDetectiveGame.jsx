import React, { useState, useEffect } from 'react';
import { Shield, Trophy, Star, AlertTriangle, CheckCircle, XCircle, Home, RotateCcw } from 'lucide-react';

const PhishDetectiveGame = () => {
  const [gameState, setGameState] = useState('menu'); // menu, playing, result
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [score, setScore] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const [userAnswers, setUserAnswers] = useState([]);
  const [streak, setStreak] = useState(0);

  const questions = [
    {
      id: 1,
      category: "Text Messages",
      scenario: "📱 You got this text message:",
      message: "🚨 URGENT! Your bank account is locked! Click this link now to unlock it: fastbank.co/unlock\n\nFrom: +1-800-URGENT",
      question: "What should you do?",
      options: [
        "Click the link right away - my account might be locked!",
        "Call my bank using the number on my bank card",
        "Reply 'STOP' to the message",
        "Share this with family to warn them"
      ],
      correctAnswer: 1,
      explanation: "Great choice! 🎉 Your bank will NEVER text you urgent links. Always call your bank directly using the phone number on your card or bank statement.",
      tips: ["Banks don't send urgent text links", "Always call your bank directly", "Don't trust unknown phone numbers"]
    },
    {
      id: 2,
      category: "Emails",
      scenario: "📧 This email landed in your inbox:",
      message: "From: Amazon Customer Service <security@amazonn.com>\n\nSubject: Your Account Will Be Closed!\n\nDear Customer,\n\nSomeone tried to hack your account! We need your password RIGHT NOW or we'll close your account in 2 hours.\n\nType your password here: ________",
      question: "What's your next move?",
      options: [
        "Type my password quickly - I don't want to lose my account!",
        "Go to Amazon's real website and log in there",
        "Reply asking for more details",
        "Call Amazon immediately"
      ],
      correctAnswer: 1,
      explanation: "Perfect! 🕵️ Real companies NEVER ask for your password in emails. Notice the fake email address 'amazonn.com' (two n's). Always go directly to the real website!",
      tips: ["Companies never ask for passwords in emails", "Check email addresses carefully", "Go to the real website yourself"]
    },
    {
      id: 3,
      category: "QR Codes",
      scenario: "🍕 At your favorite pizza place:",
      message: "You see a QR code stuck on your table that says:\n\n'SCAN HERE FOR FREE PIZZA! 🍕'\n\nBut you notice it looks different from the restaurant's other materials and seems to be a sticker placed over something else.",
      question: "What do you do?",
      options: [
        "Scan it immediately - free pizza sounds great!",
        "Ask the waiter if this is real",
        "Ignore it completely",
        "Take a photo and scan later at home"
      ],
      correctAnswer: 1,
      explanation: "Smart thinking! 🧠 Criminals often put fake QR code stickers over real ones. Restaurant staff will know if it's legitimate. Better safe than sorry!",
      tips: ["Be suspicious of 'too good to be true' offers", "Ask staff when QR codes look suspicious", "Criminals put fake stickers over real QR codes"]
    },
    {
      id: 4,
      category: "Website Links",
      scenario: "🛒 You want to shop online safely:",
      message: "Your friend sent you these shopping links. Which one looks safest for buying something?",
      question: "Pick the safest website:",
      options: [
        "http://amazone-deals.com/shop",
        "https://www.amazon.com/deals",
        "https://amazon.best-discount.net",
        "http://real-amazon.org/sale"
      ],
      correctAnswer: 1,
      explanation: "Excellent choice! 🛡️ The real Amazon website is 'amazon.com'. The others are fake websites trying to trick you. Also notice the 'https://' - that little 's' means it's secure!",
      tips: ["Stick to websites you know and trust", "Look for 'https://' not just 'http://'", "Be careful of similar-looking fake website names"]
    },
    {
      id: 5,
      category: "Phone Calls",
      scenario: "📞 Unexpected phone call:",
      message: "Someone calls and says:\n\n'Hi! I'm calling from your credit card company. We found suspicious activity on your account. To protect you, I need your card number and the 3 digits on the back right now.'",
      question: "How do you respond?",
      options: [
        "Give them the information - they're trying to help me",
        "Hang up and call the number on my credit card",
        "Ask them to call me back later",
        "Give them only part of the information"
      ],
      correctAnswer: 1,
      explanation: "Perfect! 🏆 Real credit card companies will NEVER ask for your full card details over the phone. Hang up and call the number on your actual credit card!",
      tips: ["Never give card details to callers", "Real companies don't call asking for passwords", "Always hang up and call the official number yourself"]
    },
    {
      id: 6,
      category: "Prize Scams",
      scenario: "📱 Exciting text message:",
      message: "🎉 CONGRATULATIONS! 🎉\n\nYou won $10,000 in the National Lottery!\n\nTo claim your prize, send us:\n• Your full name\n• Your address  \n• Your bank account number\n\nReply within 1 hour or lose your prize!",
      question: "What's your reaction?",
      options: [
        "Send my details quickly - I don't want to miss out!",
        "Ask my family what they think first",
        "Delete the message - this is fake",
        "Call the lottery company to check"
      ],
      correctAnswer: 2,
      explanation: "Great instincts! 🎯 You can't win a lottery you never entered! Real lotteries don't ask for bank details via text, and they don't give 1-hour deadlines.",
      tips: ["You can't win contests you never entered", "Real prizes don't need your bank details", "Scammers create fake urgency to pressure you"]
    },
    {
      id: 7,
      category: "Social Media",
      scenario: "📘 Facebook message from a 'friend':",
      message: "Hey! I'm stuck abroad and lost my wallet! The embassy can help but I need $500 for fees. Can you send money via Western Union? I'll pay you back as soon as I'm home! Please hurry!\n\n- Sarah (your friend)",
      question: "What do you do?",
      options: [
        "Send the money immediately - Sarah needs help!",
        "Call Sarah on her phone to make sure it's really her",
        "Ask other friends if they got this message too",
        "Both call Sarah AND ask other friends"
      ],
      correctAnswer: 3,
      explanation: "Brilliant detective work! 🕵️‍♀️ Scammers often hack accounts and pretend to be your friends in trouble. Always verify by calling your friend directly!",
      tips: ["Criminals hack social media accounts", "Always call your friend to verify emergency messages", "Ask other mutual friends if they got similar messages"]
    },
    {
      id: 8,
      category: "Computer Pop-ups",
      scenario: "💻 Scary computer pop-up:",
      message: "🚨 WARNING! YOUR COMPUTER IS INFECTED! 🚨\n\n27 VIRUSES FOUND!\n\nYour files will be deleted in 5 minutes!\n\nClick here to clean your computer NOW!\n\n[CLEAN MY COMPUTER] [CALL TECH SUPPORT: 1-800-FIX-NOW]",
      question: "What's your best response?",
      options: [
        "Click to clean my computer - I don't want to lose my files!",
        "Call the tech support number immediately",
        "Close the pop-up and run my regular antivirus",
        "Restart my computer right away"
      ],
      correctAnswer: 2,
      explanation: "Smart move! 🛡️ These scary pop-ups are fake! Real antivirus software doesn't work this way. Close it and use your regular antivirus program that you installed.",
      tips: ["Scary pop-ups are usually fake", "Real antivirus doesn't create panic", "Never call phone numbers from pop-ups"]
    }
  ];

  const ranks = [
    { name: "Beginner", min: 0, icon: "🌱", color: "text-green-600" },
    { name: "Learning", min: 2, icon: "📚", color: "text-blue-600" },
    { name: "Getting Good", min: 4, icon: "💪", color: "text-purple-600" },
    { name: "Scam Spotter", min: 6, icon: "👀", color: "text-orange-600" },
    { name: "Safety Expert", min: 8, icon: "🏆", color: "text-yellow-600" }
  ];

  const getCurrentRank = (score) => {
    return ranks.slice().reverse().find(rank => score >= rank.min) || ranks[0];
  };

  const handleAnswerSelect = (answerIndex) => {
    if (showFeedback) return;
    
    setSelectedAnswer(answerIndex);
    const isCorrect = answerIndex === questions[currentQuestion].correctAnswer;
    
    if (isCorrect) {
      setScore(score + 1);
      setStreak(streak + 1);
    } else {
      setStreak(0);
    }
    
    setUserAnswers([...userAnswers, {
      question: questions[currentQuestion],
      userAnswer: answerIndex,
      isCorrect
    }]);
    
    setShowFeedback(true);
  };

  const nextQuestion = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
      setSelectedAnswer(null);
      setShowFeedback(false);
    } else {
      setGameState('result');
    }
  };

  const restartGame = () => {
    setGameState('menu');
    setCurrentQuestion(0);
    setScore(0);
    setSelectedAnswer(null);
    setShowFeedback(false);
    setUserAnswers([]);
    setStreak(0);
  };

  const startGame = () => {
    setGameState('playing');
  };

  const getMotivationalMessage = (score, total) => {
    const percentage = (score / total) * 100;
    if (percentage >= 90) return "🏆 Amazing! You're a scam-fighting superhero!";
    if (percentage >= 75) return "🌟 Great job! You know how to stay safe online!";
    if (percentage >= 50) return "👍 Good work! You're learning to spot the tricks!";
    return "💪 Keep practicing! Every expert was once a beginner!";
  };

  if (gameState === 'menu') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white p-4">
        <div className="max-w-md mx-auto">
          <div className="text-center mb-8 pt-8">
            <div className="bg-blue-500 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4">
              <Shield className="w-10 h-10 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-blue-900 mb-2">Scam Spotter</h1>
            <h2 className="text-xl font-semibold text-blue-700">Quiz Game</h2>
            <p className="text-blue-600 mt-2">Learn to spot tricks and stay safe!</p>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-lg mb-6 border border-blue-100">
            <h3 className="text-lg font-semibold text-blue-900 mb-4">🎯 How It Works</h3>
            <div className="space-y-3 text-sm text-gray-700">
              <div className="flex items-start space-x-3">
                <span className="text-2xl">📱</span>
                <span>See real-life scam examples</span>
              </div>
              <div className="flex items-start space-x-3">
                <span className="text-2xl">🤔</span>
                <span>Choose the safest response</span>
              </div>
              <div className="flex items-start space-x-3">
                <span className="text-2xl">💡</span>
                <span>Learn why some choices are safer</span>
              </div>
              <div className="flex items-start space-x-3">
                <span className="text-2xl">🏆</span>
                <span>Get your safety expert ranking</span>
              </div>
            </div>
          </div>

          <button
            onClick={startGame}
            className="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-4 px-6 rounded-2xl text-lg transition-colors shadow-lg"
            style={{ backgroundColor: '#3b82f6', color: 'white' }}
            onMouseEnter={(e) => e.target.style.backgroundColor = '#2563eb'}
            onMouseLeave={(e) => e.target.style.backgroundColor = '#3b82f6'}
          >
            Start Quiz! 🚀
          </button>

          <div className="text-center mt-4 text-sm text-blue-600">
            8 questions • 5 minutes • Fun & Educational
          </div>
        </div>
      </div>
    );
  }

  if (gameState === 'playing') {
    const question = questions[currentQuestion];
    const progress = ((currentQuestion + 1) / questions.length) * 100;

    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white p-4 pt-20">
        <div className="max-w-lg mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div className="bg-blue-500 w-10 h-10 rounded-full flex items-center justify-center">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="font-bold text-blue-900">Scam Spotter</h1>
                <p className="text-sm text-blue-600">Question {currentQuestion + 1} of {questions.length}</p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-lg font-bold text-blue-900">Score: {score}</div>
              {streak > 1 && (
                <div className="text-sm text-orange-600">🔥 Streak: {streak}</div>
              )}
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mb-6">
            <div className="bg-blue-100 rounded-full h-2">
              <div 
                className="bg-blue-500 rounded-full h-2 transition-all duration-500"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>

          {/* Question Card */}
          <div className="bg-white rounded-2xl p-6 shadow-lg mb-6 border border-blue-100">
            <div className="mb-4">
              <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-3 py-1 rounded-full">
                {question.category}
              </span>
            </div>
            
            <h2 className="text-lg font-semibold text-blue-900 mb-4">{question.scenario}</h2>
            
            <div className="bg-gray-50 rounded-xl p-4 mb-6 border-l-4 border-orange-400">
              <pre className="text-sm text-gray-800 whitespace-pre-wrap font-sans leading-relaxed">
                {question.message}
              </pre>
            </div>

            <h3 className="font-semibold text-blue-900 mb-4">{question.question}</h3>

            <div className="space-y-3">
              {question.options.map((option, index) => (
                <button
                  key={index}
                  onClick={() => handleAnswerSelect(index)}
                  disabled={showFeedback}
                  className={`w-full text-left p-4 rounded-xl border-2 transition-all ${
                    showFeedback
                      ? index === question.correctAnswer
                        ? 'border-green-400 bg-green-50 text-green-800'
                        : index === selectedAnswer && selectedAnswer !== question.correctAnswer
                        ? 'border-red-400 bg-red-50 text-red-800'
                        : 'border-gray-200 bg-gray-50 text-gray-600'
                      : selectedAnswer === index
                      ? 'border-blue-400 bg-blue-50'
                      : 'border-gray-200 hover:border-blue-300 hover:bg-blue-25'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <span className="flex-shrink-0 w-6 h-6 rounded-full bg-white border-2 border-current flex items-center justify-center text-xs font-semibold">
                      {String.fromCharCode(65 + index)}
                    </span>
                    <span className="text-sm">{option}</span>
                    {showFeedback && index === question.correctAnswer && (
                      <CheckCircle className="w-5 h-5 text-green-600 ml-auto" />
                    )}
                    {showFeedback && index === selectedAnswer && selectedAnswer !== question.correctAnswer && (
                      <XCircle className="w-5 h-5 text-red-600 ml-auto" />
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Feedback */}
          {showFeedback && (
            <div className="bg-white rounded-2xl p-6 shadow-lg mb-6 border border-blue-100">
              <div className="flex items-start space-x-3 mb-4">
                {selectedAnswer === question.correctAnswer ? (
                  <CheckCircle className="w-8 h-8 text-green-600 flex-shrink-0 mt-1" />
                ) : (
                  <XCircle className="w-8 h-8 text-red-600 flex-shrink-0 mt-1" />
                )}
                <div>
                  <h3 className="font-semibold text-lg mb-2">
                    {selectedAnswer === question.correctAnswer ? "Correct! 🎉" : "Not quite right 😅"}
                  </h3>
                  <p className="text-gray-700 mb-4">{question.explanation}</p>
                  
                  <div className="bg-blue-50 rounded-lg p-3">
                    <h4 className="font-semibold text-blue-900 mb-2">💡 Remember:</h4>
                    <ul className="space-y-1">
                      {question.tips.map((tip, index) => (
                        <li key={index} className="text-sm text-blue-800 flex items-start space-x-2">
                          <span className="text-blue-500 mt-1">•</span>
                          <span>{tip}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>

              <button
                onClick={nextQuestion}
                className="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-3 px-6 rounded-xl transition-colors"
                style={{ backgroundColor: '#3b82f6', color: 'white' }}
                onMouseEnter={(e) => e.target.style.backgroundColor = '#2563eb'}
                onMouseLeave={(e) => e.target.style.backgroundColor = '#3b82f6'}
              >
                {currentQuestion < questions.length - 1 ? 'Next Question →' : 'See Results! 🏆'}
              </button>
            </div>
          )}
        </div>
      </div>
    );
  }

  if (gameState === 'result') {
    const rank = getCurrentRank(score);
    const percentage = Math.round((score / questions.length) * 100);

    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white p-4">
        <div className="max-w-lg mx-auto">
          {/* Header */}
          <div className="text-center mb-8 pt-8">
            <div className="bg-blue-500 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4">
              <Trophy className="w-10 h-10 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-blue-900 mb-2">Quiz Complete!</h1>
            <p className="text-lg text-blue-600">{getMotivationalMessage(score, questions.length)}</p>
          </div>

          {/* Score Card */}
          <div className="bg-white rounded-2xl p-6 shadow-lg mb-6 border border-blue-100">
            <div className="text-center mb-6">
              <div className="text-6xl mb-2">{rank.icon}</div>
              <h2 className={`text-2xl font-bold mb-2 ${rank.color}`}>{rank.name}</h2>
              <div className="text-3xl font-bold text-blue-900">{score}/{questions.length}</div>
              <div className="text-lg text-blue-600">{percentage}% Correct</div>
            </div>

            <div className="bg-blue-50 rounded-xl p-4">
              <h3 className="font-semibold text-blue-900 mb-3">📊 Your Results:</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-blue-800">Questions Answered:</span>
                  <span className="font-semibold">{questions.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-green-700">Correct Answers:</span>
                  <span className="font-semibold text-green-800">{score}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-red-700">Incorrect Answers:</span>
                  <span className="font-semibold text-red-800">{questions.length - score}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Key Takeaways */}
          <div className="bg-white rounded-2xl p-6 shadow-lg mb-6 border border-blue-100">
            <h3 className="text-xl font-semibold text-blue-900 mb-4">🎯 Key Safety Tips:</h3>
            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <span className="text-2xl">🏦</span>
                <span className="text-sm text-gray-700">Banks and companies never ask for passwords via text or email</span>
              </div>
              <div className="flex items-start space-x-3">
                <span className="text-2xl">📞</span>
                <span className="text-sm text-gray-700">When in doubt, hang up and call official numbers yourself</span>
              </div>
              <div className="flex items-start space-x-3">
                <span className="text-2xl">🔗</span>
                <span className="text-sm text-gray-700">Only trust websites you know and type URLs yourself</span>
              </div>
              <div className="flex items-start space-x-3">
                <span className="text-2xl">🎁</span>
                <span className="text-sm text-gray-700">Be suspicious of unexpected prizes or urgent messages</span>
              </div>
              <div className="flex items-start space-x-3">
                <span className="text-2xl">👥</span>
                <span className="text-sm text-gray-700">Verify emergency messages by calling your friends directly</span>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="space-y-3">
            <button
              onClick={restartGame}
              className="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-4 px-6 rounded-2xl text-lg transition-colors shadow-lg flex items-center justify-center space-x-2"
              style={{ backgroundColor: '#3b82f6', color: 'white' }}
              onMouseEnter={(e) => e.target.style.backgroundColor = '#2563eb'}
              onMouseLeave={(e) => e.target.style.backgroundColor = '#3b82f6'}
            >
              <RotateCcw className="w-5 h-5" />
              <span>Play Again</span>
            </button>
            
            <button
              onClick={() => window.history.back()}
              className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold py-4 px-6 rounded-2xl text-lg transition-colors flex items-center justify-center space-x-2"
            >
              <Home className="w-5 h-5" />
              <span>Back to Home</span>
            </button>
          </div>

          <div className="text-center mt-6 text-sm text-blue-600">
            Share your knowledge with friends and family! 💙
          </div>
        </div>
      </div>
    );
  }
};

export default PhishDetectiveGame;