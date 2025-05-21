#ifndef HANAMIKOJI_WEB_SOCKET_CLIENT_H_INCLUDED
#define HANAMIKOJI_WEB_SOCKET_CLIENT_H_INCLUDED

#include <asio.hpp>
#include <nlohmann/json.hpp>
#include <websocketpp/client.hpp>
#include <websocketpp/config/asio_no_tls_client.hpp>

#include <condition_variable>
#include <iostream>
#include <mutex>
#include <queue>
#include <string>
#include <thread>

using websocketpp::connection_hdl;
typedef websocketpp::client<websocketpp::config::asio_client> client;

using json = nlohmann::json;

using websocketpp::connection_hdl;
using json = nlohmann::json;

class WebSocketClient
{
public:
  WebSocketClient()
  {
    client_.init_asio();

    client_.set_open_handler([this](connection_hdl hdl) {
      this->hdl_ = hdl;
      connected_ = true;
    });

    client_.set_message_handler(
        [this](connection_hdl, websocketpp::client<websocketpp::config::asio_client>::message_ptr msg) {
          std::unique_lock<std::mutex> lock(queue_mutex_);
          message_queue_.push(msg->get_payload());
          queue_cv_.notify_one();
        });
  }

  ~WebSocketClient()
  {
    if (client_thread_.joinable()) {
      client_.stop();
      client_thread_.join();
    }
  }

  void connect(const std::string& uri)
  {
    while (true) {
      websocketpp::lib::error_code ec;
      auto con = client_.get_connection(uri, ec);
      if (ec) {
        std::cerr << "[ERROR] Creating connection failed: " << ec.message() << std::endl;
        std::this_thread::sleep_for(std::chrono::seconds(1));
        continue;
      }

      connected_ = false;  // Reset before trying
      client_.connect(con);

      // Start client loop thread if not already running
      if (!client_thread_.joinable()) {
        client_thread_ = std::thread([this]() { client_.run(); });
      }

      // Wait briefly for on_open handler
      int wait_ms = 0;
      while (!connected_ && wait_ms < 2000) {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        wait_ms += 100;
      }

      if (connected_) {
        std::cout << "[INFO] Connected to WebSocket server." << std::endl;
        break;
      } else {
        std::cerr << "[WARN] Connection failed. Retrying..." << std::endl;
        std::this_thread::sleep_for(std::chrono::seconds(1));
      }
    }
  }
  
  void send_message(const json& msg)
  {
    std::string payload = msg.dump();
    websocketpp::lib::error_code ec;
    client_.send(hdl_, payload, websocketpp::frame::opcode::text, ec);
    if (ec) {
      std::cerr << "[ERROR] Send failed: " << ec.message() << std::endl;
    }
  }

  json receive_message()
  {
    std::unique_lock<std::mutex> lock(queue_mutex_);
    queue_cv_.wait(lock, [this] { return !message_queue_.empty(); });

    std::string payload = message_queue_.front();
    message_queue_.pop();
    return json::parse(payload);
  }

private:
  websocketpp::client<websocketpp::config::asio_client> client_;
  connection_hdl hdl_;
  std::thread client_thread_;
  bool connected_ = false;

  std::queue<std::string> message_queue_;
  std::mutex queue_mutex_;
  std::condition_variable queue_cv_;
};

#endif
