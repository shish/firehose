// based on:
// http://www.badgerr.co.uk/2011/06/20/golang-away-tcp-chat-server/

package main

// Imports required packages
import "fmt"
import "net"
import "container/list"
import "bytes"

// Defines a Client with a name and connection object, and
// some channels for sending and receiving text.
// Also holds a pointer to the "global" list of all connected clients
type Client struct {
	Name string
	Incoming chan string
	Outgoing chan string
	Conn net.Conn
	Quit chan bool
	ClientList *list.List
}

// Defines a read function for a client, reading from the connection into
// a buffer passed in. Returns true if read was successful, false otherwise
func (c *Client) Read(buffer []byte) bool {
	bytesRead, error := c.Conn.Read(buffer)
	if error != nil {
		c.Close()
		Log(error)
		return false
	}
	//Log("Read ", bytesRead, " bytes")
	return true
}

// Closes a client connection and removes it from the client list
func (c *Client) Close() {
	c.Quit <- true
	c.Conn.Close()
	c.RemoveMe()
}

// Comparason function to easily check equality with another client
// based on the name and connection
func (c *Client) Equal(other *Client) bool {
	if bytes.Equal([]byte(c.Name), []byte(other.Name)) {
		if c.Conn == other.Conn {
			return true
		}
	}
	return false
}

// Removes this client from the client list
func (c *Client) RemoveMe() {
	for entry := c.ClientList.Front(); entry != nil; entry = entry.Next() {
		client := entry.Value.(Client)
		if c.Equal(&client) {
			Log("RemoveMe: ", c.Name)
			c.ClientList.Remove(entry)
		}
	}
}

// Logging function, currently a wrapper arounf Println, but could be 
// replaced with file based output
func Log(v ...interface{}) {
	fmt.Println(v...)
}

// Server listener goroutine - waits for data from the incoming channel
// (each client.Outgoing stores this), and passes it to each client.Incoming channel
func IOHandler(Incoming <-chan string, clientList *list.List) {
	for {
		//Log("IOHandler: Waiting for input")
		input := <-Incoming
		//Log("IOHandler: Handling ", input)
		for e := clientList.Front(); e != nil; e = e.Next() {
			client := e.Value.(Client)
			client.Incoming <-input
		}
	}
}

// Client reading goroutine - reads incoming data from the tcp socket, 
// sends it to the client.Outgoing channel (to be picked up by IOHandler)
func ClientReader(client *Client) {
	buffer := make([]byte, 2048)

	for client.Read(buffer) {
		if bytes.Equal(buffer, []byte("/quit")) {
			client.Close()
			break
		}
		//Log("ClientReader received ", client.Name, "> ", string(buffer))
		//send := client.Name+"> "+string(buffer)
		send := string(buffer)
		client.Outgoing <- send
		for i := 0; i < 2048; i++ {
			buffer[i] = 0x00
		}
	}

	//client.Outgoing <- client.Name + " has left chat"
	//Log("ClientReader stopped for ", client.Name)
}

// Client sending goroutine - waits for data to be sent over client.Incoming
// (from IOHandler), then sends it over the socket
func ClientSender(client *Client) {
	for {
		select {
			case buffer := <-client.Incoming:
				//Log("ClientSender sending ", string(buffer), " to ", client.Name)
				count := 0
				for i := 0; i < len(buffer); i++ {
					if buffer[i] == 0x00 {
						break
					}
					count++
				}
				//Log("Send size: ", count)
				client.Conn.Write([]byte(buffer)[0:count])
			case <-client.Quit:
				//Log("Client ", client.Name, " quitting")
				client.Conn.Close()
				break
		}
	}
}

// Creates a new client object for each new connection using the name sent by the client,
// then starts the ClientSender and ClientReader goroutines to handle the IO
func ClientHandler(conn net.Conn, ch chan string, clientList *list.List) {
	/*
	buffer := make([]byte, 1024)
	bytesRead, error := conn.Read(buffer)
	if error != nil {
		Log("Client connection error: ", error)
	}
	name := string(buffer[0:bytesRead])
	*/
	name := conn.RemoteAddr().String()
	newClient := &Client{name, make(chan string), ch, conn, make(chan bool), clientList}

	go ClientSender(newClient)
	go ClientReader(newClient)
	clientList.PushBack(*newClient)
	//ch <-string(name + " has joined the chat")
}

// Main: Starts a TCP server and waits infinitely for connections
func main() {
	Log("Firehose Server Starting")

	clientList := list.New()
	in := make(chan string)
	go IOHandler(in, clientList)

	service := "0.0.0.0:9988"
	tcpAddr, error := net.ResolveTCPAddr("tcp", service)
	if error != nil {
		Log("Error: Could not resolve address")
	} else {
		netListen, error := net.Listen(tcpAddr.Network(), tcpAddr.String())
		if error != nil {
			Log(error)
		} else {
			defer netListen.Close()

			for {
				Log("Waiting for clients")
				connection, error := netListen.Accept()
				if error != nil {
					Log("Client error: ", error)
				} else {
					go ClientHandler(connection, in, clientList)
				}
			}
		}
	}
}
