import React, { useState } from 'react';

const PinInput = ({ onPinEntered }) => {
  const [pin, setPin] = useState('');

  const handlePinChange = (e) => {
    setPin(e.target.value);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onPinEntered(pin);
  };

  return (
    <div className="pin-input-container">
      <form onSubmit={handleSubmit}>
        <label>
          Enter PIN:
          <input type="password" value={pin} onChange={handlePinChange} />
        </label>
        <button type="submit">Submit</button>
      </form>
    </div>
  );
};

export default PinInput;
