/*
  Arduino Sign Language Recognition Receiver
  Recibe predicciones vía serial y ejecuta acciones de hardware
  
  Conexiones:
  - LEDs: Pines 2-11 (A-I, unknown)
  - Buzzer: Pin 12
  - Servos: Pines 9, 10 (PWM)
  - Potenciómetro: Pin A0 (opcional para ajustes)
  
  Comunicación:
  - Baud rate: 9600
  - Formato: "comando:parametro1:parametro2"
*/

// Pines para LEDs de cada seña
const int LED_A = 2;
const int LED_B = 3;
const int LED_C = 4;
const int LED_D = 5;
const int LED_E = 6;
const int LED_F = 7;
const int LED_G = 8;
const int LED_H = 9;
const int LED_I = 10;
const int LED_UNKNOWN = 11;

// Pines para actuadores
const int BUZZER = 12;
const int SERVO_1 = 9;  // Compartido con LED_H (alternar)
const int SERVO_2 = 10; // Compartido con LED_I (alternar)

// Variables de estado
bool ledStates[12] = {false}; // Estado de cada LED
int currentMode = 0; // 0: LEDs, 1: Servos
unsigned long lastActivity = 0;
const int ACTIVITY_TIMEOUT = 5000; // 5 segundos sin actividad

// Servo library (requiere incluir Servo.h)
#include <Servo.h>
Servo servo1, servo2;

void setup() {
  Serial.begin(9600);
  
  // Configurar pines LED como salida
  for (int i = LED_A; i <= LED_UNKNOWN; i++) {
    pinMode(i, OUTPUT);
    digitalWrite(i, LOW);
    ledStates[i - LED_A] = false;
  }
  
  // Configurar pines de actuadores
  pinMode(BUZZER, OUTPUT);
  digitalWrite(BUZZER, LOW);
  
  // Inicializar servos
  servo1.attach(SERVO_1);
  servo2.attach(SERVO_2);
  servo1.write(90); // Posición neutra
  servo2.write(90);
  
  // LED de estado inicial
  digitalWrite(LED_UNKNOWN, HIGH);
  delay(500);
  digitalWrite(LED_UNKNOWN, LOW);
  
  Serial.println("Arduino Sign Recognition Ready");
  Serial.println("Commands: gesture_X:conf, led_on:X, led_off:X, buzzer:freq:ms, servo:X:angle, test, status");
}

void loop() {
  // Verificar timeout de actividad
  if (millis() - lastActivity > ACTIVITY_TIMEOUT) {
    // Apagar todo después de 5 segundos de inactividad
    allLedsOff();
    servosToNeutral();
    lastActivity = millis();
  }
  
  // Procesar comandos serial
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    if (input.length() > 0) {
      processCommand(input);
      lastActivity = millis();
    }
  }
  
  delay(10); // Pequeña pausa para estabilidad
}

void processCommand(String input) {
  // Parsear comando
  int colon1 = input.indexOf(':');
  int colon2 = input.indexOf(':', colon1 + 1);
  
  String command = "";
  String param1 = "";
  String param2 = "";
  
  if (colon1 > 0) {
    command = input.substring(0, colon1);
    
    if (colon2 > 0) {
      param1 = input.substring(colon1 + 1, colon2);
      param2 = input.substring(colon2 + 1);
    } else {
      param1 = input.substring(colon1 + 1);
    }
  } else {
    command = input;
  }
  
  // Ejecutar comando
  if (command == "gesture_A" || command == "gesture_B" || command == "gesture_C" ||
      command == "gesture_D" || command == "gesture_E" || command == "gesture_F" ||
      command == "gesture_G" || command == "gesture_H" || command == "gesture_I") {
    executeGesture(command, param1.toFloat());
  }
  else if (command == "no_gesture") {
    executeGesture(command, param1.toFloat());
  }
  else if (command == "led_on") {
    int ledPin = param1.toInt();
    ledOn(ledPin);
  }
  else if (command == "led_off") {
    int ledPin = param1.toInt();
    ledOff(ledPin);
  }
  else if (command == "buzzer") {
    int freq = param1.toInt();
    int duration = param2.toInt();
    playBuzzer(freq, duration);
  }
  else if (command == "servo") {
    int servoNum = param1.toInt();
    int angle = param2.toInt();
    moveServo(servoNum, angle);
  }
  else if (command == "test") {
    runTestSequence();
  }
  else if (command == "status") {
    sendStatus();
  }
  else if (command == "disconnect") {
    Serial.println("Arduino disconnecting");
    allLedsOff();
    servosToNeutral();
  }
  else {
    Serial.println("Unknown command: " + command);
  }
}

void executeGesture(String gesture, float confidence) {
  // Apagar todos los LEDs primero
  allLedsOff();
  
  // Mapear gestos a LEDs y acciones
  int ledPin = LED_UNKNOWN;
  int buzzerFreq = 0;
  int servoAction = -1;
  
  if (gesture == "gesture_A") {
    ledPin = LED_A;
    buzzerFreq = 440; // Nota A4
    servoAction = 0; // Servo 1 a 0 grados
  }
  else if (gesture == "gesture_B") {
    ledPin = LED_B;
    buzzerFreq = 494; // Nota B4
    servoAction = 1; // Servo 1 a 180 grados
  }
  else if (gesture == "gesture_C") {
    ledPin = LED_C;
    buzzerFreq = 523; // Nota C5
    servoAction = 2; // Servo 2 a 0 grados
  }
  else if (gesture == "gesture_D") {
    ledPin = LED_D;
    buzzerFreq = 587; // Nota D5
    servoAction = 3; // Servo 2 a 180 grados
  }
  else if (gesture == "gesture_E") {
    ledPin = LED_E;
    buzzerFreq = 659; // Nota E5
  }
  else if (gesture == "gesture_F") {
    ledPin = LED_F;
    buzzerFreq = 698; // Nota F5
  }
  else if (gesture == "gesture_G") {
    ledPin = LED_G;
    buzzerFreq = 784; // Nota G5
  }
  else if (gesture == "gesture_H") {
    ledPin = LED_H;
    buzzerFreq = 880; // Nota A5
  }
  else if (gesture == "gesture_I") {
    ledPin = LED_I;
    buzzerFreq = 988; // Nota B5
  }
  else if (gesture == "no_gesture") {
    ledPin = LED_UNKNOWN;
    buzzerFreq = 0;
  }
  
  // Activar LED correspondiente
  if (ledPin >= LED_A && ledPin <= LED_UNKNOWN) {
    digitalWrite(ledPin, HIGH);
    ledStates[ledPin - LED_A] = true;
  }
  
  // Sonido de confirmación si confianza alta
  if (confidence > 0.8 && buzzerFreq > 0) {
    playBuzzer(buzzerFreq, 100);
  }
  
  // Acción de servo si se especificó
  if (servoAction >= 0 && servoAction <= 3) {
    int angle = (servoAction % 2 == 0) ? 0 : 180;
    int servoNum = (servoAction < 2) ? 1 : 2;
    moveServo(servoNum, angle);
  }
  
  // Debug output
  Serial.print("Gesture: ");
  Serial.print(gesture);
  Serial.print(" (");
  Serial.print(confidence, 2);
  Serial.print(") -> LED: ");
  Serial.print(ledPin);
  if (buzzerFreq > 0) {
    Serial.print(", Buzzer: ");
    Serial.print(buzzerFreq);
  }
  Serial.println();
}

void ledOn(int ledPin) {
  if (ledPin >= LED_A && ledPin <= LED_UNKNOWN) {
    digitalWrite(ledPin, HIGH);
    ledStates[ledPin - LED_A] = true;
    Serial.print("LED ON: ");
    Serial.println(ledPin);
  }
}

void ledOff(int ledPin) {
  if (ledPin >= LED_A && ledPin <= LED_UNKNOWN) {
    digitalWrite(ledPin, LOW);
    ledStates[ledPin - LED_A] = false;
    Serial.print("LED OFF: ");
    Serial.println(ledPin);
  }
}

void allLedsOff() {
  for (int i = LED_A; i <= LED_UNKNOWN; i++) {
    digitalWrite(i, LOW);
    ledStates[i - LED_A] = false;
  }
}

void playBuzzer(int frequency, int durationMs) {
  if (frequency > 0 && durationMs > 0) {
    tone(BUZZER, frequency, durationMs);
    delay(durationMs + 10); // Pequeña pausa después del tono
    noTone(BUZZER);
  }
}

void moveServo(int servoNum, int angle) {
  if (servoNum == 1) {
    servo1.write(constrain(angle, 0, 180));
  } else if (servoNum == 2) {
    servo2.write(constrain(angle, 0, 180));
  }
  
  Serial.print("Servo ");
  Serial.print(servoNum);
  Serial.print(" -> ");
  Serial.print(angle);
  Serial.println("°");
  
  delay(15); // Pequeña pausa para movimiento del servo
}

void servosToNeutral() {
  servo1.write(90);
  servo2.write(90);
  delay(100);
}

void runTestSequence() {
  Serial.println("Running test sequence...");
  
  // Test LEDs
  for (int i = LED_A; i <= LED_UNKNOWN; i++) {
    digitalWrite(i, HIGH);
    delay(200);
    digitalWrite(i, LOW);
    delay(100);
  }
  
  // Test buzzer
  playBuzzer(1000, 200);
  delay(300);
  playBuzzer(1500, 200);
  delay(300);
  
  // Test servos
  moveServo(1, 0);
  delay(500);
  moveServo(1, 180);
  delay(500);
  moveServo(1, 90);
  delay(500);
  moveServo(2, 0);
  delay(500);
  moveServo(2, 180);
  delay(500);
  moveServo(2, 90);
  
  Serial.println("Test sequence completed");
}

void sendStatus() {
  Serial.println("=== Arduino Status ===");
  Serial.print("LEDs: ");
  for (int i = 0; i < 10; i++) {
    Serial.print(ledStates[i] ? "1" : "0");
  }
  Serial.println();
  Serial.print("Servo 1: ");
  Serial.print(servo1.read());
  Serial.println("°");
  Serial.print("Servo 2: ");
  Serial.print(servo2.read());
  Serial.println("°");
  Serial.print("Mode: ");
  Serial.println(currentMode == 0 ? "LEDs" : "Servos");
  Serial.print("Uptime: ");
  Serial.print(millis() / 1000);
  Serial.println("s");
  Serial.println("==================");
}
