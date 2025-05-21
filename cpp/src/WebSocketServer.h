#ifndef HANAMIKOJI_WEB_SOCKET_SERVER_H_INCLUDED
#define HANAMIKOJI_WEB_SOCKET_SERVER_H_INCLUDED

#include <asio.hpp>
#include <nlohmann/json.hpp>
#include <websocketpp/config/asio_no_tls.hpp>
#include <websocketpp/server.hpp>

#include <condition_variable>
#include <iostream>
#include <mutex>
#include <queue>
#include <string>
#include <thread>

using json = nlohmann::json;
using websocketpp::connection_hdl;
typedef websocketpp::server<websocketpp::config::asio> server;

class WebSocketServer
{
public:
  WebSocketServer(uint16_t port = 8765) : port_(port), connected_(false)
  {
    server_.init_asio();

    server_.set_open_handler([this](connection_hdl hdl) {
      {
        std::lock_guard<std::mutex> lock(hdl_mutex_);
        hdl_ = hdl;
        connected_ = true;
      }
      std::cout << "[INFO] Server connected." << std::endl;
    });

    server_.set_message_handler([this](connection_hdl, server::message_ptr msg) {
      std::unique_lock<std::mutex> lock(queue_mutex_);
      message_queue_.push(msg->get_payload());
      queue_cv_.notify_one();
    });

    server_thread_ = std::thread([this]() {
      server_.listen(port_);
      server_.start_accept();
      server_.run();
    });

    // Wait for connection
    std::cout << "[INFO] Waiting for WebSocket server to connect on port " << port_ << "..." << std::endl;
    while (!connected_) {
      std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
  }

  ~WebSocketServer()
  {
    server_.stop_listening();
    server_.stop();
    if (server_thread_.joinable()) {
      server_thread_.join();
    }
  }

  void send_message(const json& msg)
  {
    std::string payload = msg.dump();
    websocketpp::lib::error_code ec;

    std::lock_guard<std::mutex> lock(hdl_mutex_);
    server_.send(hdl_, payload, websocketpp::frame::opcode::text, ec);
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
  server server_;
  std::thread server_thread_;
  uint16_t port_;
  connection_hdl hdl_;
  std::mutex hdl_mutex_;
  bool connected_;

  std::queue<std::string> message_queue_;
  std::mutex queue_mutex_;
  std::condition_variable queue_cv_;
};

#endif